'''
Author: Xin Du
Date: 2024-11-27 21:33:57
LastEditors: Xin Du
LastEditTime: 2024-12-17 15:59:43
Description: Programable logic controller
'''

import json
import os
import time
import random


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Cyber_simulation.PIController import PLC1_control, PLC2_control, write_data_to_actors, read_sensors_data, read_work_condition, file_update_time_to_now
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
from utils.modbus import generate_random_floats,  float32_to_modbus_registers, decode_float_values, write_data_to_modbus_device, read_data_from_modbus_device
from utils.utils import get_system_config, get_system_state, show_exp_data, get_data_id, write_config


def read_json_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return None


def write_json_file(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f)


class PLC:
    
    def __init__(self, ip, port, slave, name = 'PLC'):
        dbs_server_port, ews_server_port, plc_client_port = port
        print(f'dbs_server_port: {dbs_server_port}  ews_server_port: {ews_server_port} plc_client_port: {plc_client_port} slave: {slave}')
        
        self.dbs_client = ModbusTcpClient(ip, port=dbs_server_port, source_address=(ip, plc_client_port))
        
        self.ews_client = ModbusTcpClient(ip, port=ews_server_port, source_address=(ip, plc_client_port+1), timeout=10)
        
        self.slave = slave
        self.name = name
        self.sim_cnt = 0
        
        
        print('> --- Create PLC Modbus TCP client ---')
        print(f'{self.name} - IP : {ip} - Port : {plc_client_port} ')
        print(f'DBS - Port : {dbs_server_port} - Slave : {slave}')
        
        # 获得PLC设备控制回路设定值与执行器传感器状态
        sim_cfg = get_system_config('simulation')
        self.sim_period = sim_cfg['sim_period']
        self.sim_state = sim_cfg['sim_state']
        self.sim_end_time = sim_cfg['sim_end_time']
        
        if self.name == 'PLC1':
            self.sp_data = [246.0869582, 530.8807979, 756.1036239]
        else:
            self.sp_data = [70.3336176]
        self.old_sp_data = 0
        self.SP_ID, self.FV_XI_ID = get_data_id(name)


    def receive_data_from_ews(self, interval):
        if self.sim_state == 'A_MITM' and self.name == 'PLC1':
            PLC_interval = interval
            dos_requests = 1
            
        elif self.sim_state == 'A_FDI' and self.name == 'PLC2':
            PLC_interval = 0.8 * interval
            dos_requests = 1
            
        elif self.sim_state == 'A_DOS' and self.name == 'PLC2' and self.sim_cnt >= 10:
            dos_interval = 2 * interval
            dos_requests = 60
            PLC_interval = 0
            
        else:
            PLC_interval = 0
            dos_interval = 0
            dos_requests = 1
            
        time.sleep(PLC_interval)
        sp_data_num = 2 * len(self.SP_ID)
        
        for _ in range(dos_requests):
            
            self.sp_data = read_data_from_modbus_device(
                self.ews_client,
                sp_data_num,
                self.slave,
                client_name=self.name,
                target_name='EWS'
            )
            if dos_requests > 1:
                print('>>> DoS Attack on!')
                self.sp_data = self.old_sp_data
                time.sleep(dos_interval / dos_requests)
                PLC_interval = dos_interval
            else:
                self.old_sp_data = self.sp_data
                print("self.old_sp_data: ", self.old_sp_data)

        print("self.sp_data: ", self.sp_data)
        print(f"> {self.name} - Receive setpoint from EWS ：", self.sp_data)
        return PLC_interval


    def write_data_to_dbs(self, measure_data):
        """Send sensor and actuator data to DBS"""

        # 上传传感器与执行器状态
        if self.sim_state == 'F_SF':
            if self.sim_cnt > 10 and self.sim_cnt < 60:
                if self.name == 'PLC2':
                    measure_data[1] = 2700
                    print(f'> PLC2 ： Sensor FI1 failure')
            
            elif self.sim_cnt >= 60:
                if self.name == 'PLC1':
                    measure_data[12] = 24
                    print(f'> PLC1 ：Sensor PI1 failure')
                    
        write_data_to_modbus_device(
            self.dbs_client, 
            measure_data, 
            self.slave,
            client_name = self.name,
            target_name = 'DBS'
        )
        
        print(f'> {self.name} - send field data to DBS：', measure_data)
        show_exp_data(self.FV_XI_ID, measure_data)
        print()


    def run(self):
        
        interval = self.sim_period * 1 / 5
        PLC_interval = 0
        
        work_condition_df = read_work_condition()
        
        errord = [0.136692017830002, -0.0707331131770190, -0.352870002514544, -2.77937044322705]
        PI_sensors = [69.99924884, 392.00019503, 549.99917972, 675.01631067]
        
        MV_SP = work_condition_df.iloc[self.sim_cnt, 4 : ].to_list()
        
        Actor_data_file_path = f'./data/FCC_json/{self.name}_actors.json'
        Sensor_data_file_path = f'./data/FCC_json/{self.name}_sensors.json'
        
        current_time = time.time()
        if self.name == 'PLC1':
            json_actors = [50.0, 50.0, 50.0]
        else:
            json_actors = 50.0
        
        write_json_data = {
            "actors"      : json_actors ,
            "MV_SP"       : MV_SP  ,
            "sim_cnt"     : self.sim_cnt,
        }
        write_json_file(Actor_data_file_path, write_json_data)
        print("> Created PLC1_actors.json and PLC2_actors.json with initial data")
        
        measure_data = [0 for _ in range(len(self.FV_XI_ID))]
        TIMEOUT = 15
        controller_sim_start = False
        waiting_FCC_connection_time = 0
        WAITING_FCC_TIMEOUT = 15
        
        while True:
            
            print(10*'**********')
            print(f">>> Simulation condition: {self.sim_state} \n")
            
            if self.sim_cnt > self.sim_end_time + 1:
                break
            
            if abs(file_update_time_to_now(Sensor_data_file_path)) > TIMEOUT:
                print(f">>> FCC simulation not updated, waiting for updates...  {waiting_FCC_connection_time} s")
                waiting_FCC_connection_time += 1
            else:
                try:
                    sensor_data = read_json_file(Sensor_data_file_path)
                except FileNotFoundError:
                    print(f'> Warning: Sensor JSON data file not found, waiting for next read')                
                except Exception as e:
                    print(f'> Warning: Unknown error occurred while reading sensor JSON data: {e}')
                waiting_FCC_connection_time = 0
                # 信息域仿真计数与物理域保持同步
                if sensor_data["sim_cnt"] == self.sim_cnt:
                    print('>>> PLC simulation counting update')
                    print(f'> Controller simulation counting: {self.sim_cnt}，FCC simulation counting: {sensor_data["sim_cnt"]} \n')
                    self.sim_cnt += 1
                    controller_sim_start = True
                
                if len(sensor_data['sensors']) == 0:
                    controller_sim_start = False
                    print('>>> Sensor data not updated, waiting...')
                    
            if waiting_FCC_connection_time > WAITING_FCC_TIMEOUT:
                print("> FCC simulation timeout connection, simulation stopped")

            # 进行控制器仿真步进
            if controller_sim_start:
                controller_sim_start = False
                print('\n', 15*'=======')
                print(f'> Controller {self.name} start up--simulation time -- {self.sim_cnt} -- ')
                PLC_SP = self.sp_data
                MV_SP = work_condition_df.iloc[self.sim_cnt, 4 : ].to_list()

                if len(sensor_data['sensors']) == 0:
                    XI_ID = get_data_id(self.name, mode = 'XI')
                    sensors = [0 for _ in range(len(XI_ID))]
                else:
                    sensors = sensor_data['sensors']
                
                if self.name == 'PLC1':
                    print(f'> {self.name} perform PI operation')
                    PI_sensors = [sensors[0], sensors[1], sensors[2]]
                    V8, V10, V11, ETC4, ETC5, ETC6 = PLC1_control(PI_sensors, PLC_SP, errord, self.sim_cnt)
                    errord[1], errord[2], errord[3] = ETC4, ETC5, ETC6
                    measure_data = [V8, V10, V11] + sensors
                    json_actor = []
                    json_actor.append(V8)
                    json_actor.append(V10)
                    json_actor.append(V11)
                    sim_cfg = get_system_config('simulation')
                    sim_cfg['sim_time'] = self.sim_cnt
                    write_config(sim_cfg, 'simulation')
                
                elif self.name == 'PLC2':
                    print(f'> {self.name} perform PI operation')
                    PI_sensors = sensors[1]  # LI1
                    V9, ELC2 = PLC2_control(PI_sensors, PLC_SP, errord, self.sim_cnt)
                    errord[0] = ELC2
                    measure_data = [V9] + sensors
                    json_actor = V9
                    
    
                write_json_data['MV_SP'] = MV_SP
                write_json_data['actors'] = json_actor
                
            write_json_data['sim_cnt'] = self.sim_cnt    
            write_json_file(Actor_data_file_path, write_json_data)

            try:
                if self.sim_state == 'A_MITM' and self.name == 'PLC1'  and 10 <= self.sim_cnt:
                    self.write_data_to_dbs(measure_data)
                    PLC_interval = self.receive_data_from_ews(interval)
                    time.sleep(2 * interval)
                    PLC_interval = self.receive_data_from_ews(interval)
                    PLC_interval = PLC_interval * 2 + interval
                if self.sim_state == 'A_FDI' and self.name == 'PLC2'  and 10 <= self.sim_cnt:
                    self.write_data_to_dbs(measure_data)
                    PLC_interval = self.receive_data_from_ews(interval)
                    time.sleep(1 * interval)
                    PLC_interval = self.receive_data_from_ews(interval)
                    PLC_interval = PLC_interval * 2 + interval
                
                elif self.sim_state == 'A_DOS' and self.name == 'PLC2' and 10 <= self.sim_cnt:
                    # Stop PLC2 from sending data to EWS and DBS
                    PLC_interval = self.receive_data_from_ews(interval)
                    time.sleep(interval)

                elif self.sim_state == 'F_CF' and self.name == 'PLC1' and  10 <= self.sim_cnt and self.sim_cnt < 60:
                    # Stop PLC1 from sending data to EWS and DBS
                    time.sleep(interval)
                elif self.sim_state == 'F_CF' and self.name == 'PLC2' and 60 <= self.sim_cnt:
                    # Stop PLC1 from sending data to EWS and DBS
                    time.sleep(interval)
                else:
                    self.write_data_to_dbs(measure_data)
                    time.sleep(interval)
                    PLC_interval = self.receive_data_from_ews(interval)
                    
            # except ConnectionException:
            #     print("PLC: Connection to DBS or EWS failed, retrying ...")
            except Exception as e:
                    print(f'> Warning: PLC: Connection to DBS or EWS failed, retrying .. {e}')
            time.sleep(self.sim_period - interval - PLC_interval)
            