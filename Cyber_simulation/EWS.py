
'''
Author: Xin Du
Date: 2023-04-11 11:44:55
LastEditors: Xin Du
LastEditTime: 2024-12-16 21:42:25
Description:  Engineering Workstation
'''
import random
import struct

import time
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.datastore import ModbusServerContext
from pymodbus.exceptions import ConnectionException

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.modbus import create_server_context, decode_float_values, run_modbus_server, generate_random_floats, write_data_to_modbus_device, read_data_from_modbus_device, float32_to_modbus_registers, decode_float_values
from utils.utils import get_data_id, get_system_config, get_system_state, show_exp_data


class EWS:
    def __init__(self, ip, port, slave, name = 'EWS'):
        self.slave = slave
        self.name = name

        dbs_server_port, ews_server_port, ews_client_port = port
        
        self.ews_client = ModbusTcpClient(ip, port=dbs_server_port, source_address=(ip, ews_client_port))

        print(f'ip: {ip}, dbs_server_port: {dbs_server_port}, ews_server_port: {ews_server_port}, ews_client_port: {ews_client_port} ')

        self.store = create_server_context()
        run_modbus_server(context = self.store, ip = ip,  port = ews_server_port)
        
        sim_cfg = get_system_config('simulation')
        self.sim_period = sim_cfg['sim_period']
        self.sim_state = sim_cfg['sim_state']

        self.DBS_SP_ID, self.DBS_FV_XI_ID = get_data_id('DBS')
        self.sp_data = [50, 50, 50, 50]

        self.plc_list = ['PLC1', 'PLC2']
        self.sim_cnt = 0


    def receive_data_from_his(self):
        his_result  = self.store[4].getValues(3, 0, 2 * len(self.DBS_SP_ID)) 
        self.sp_data = decode_float_values(his_result)
        print('\n', 15*'-----')
        print("\n EWS: Read data from HIS: ", self.sp_data)
        show_exp_data(self.DBS_SP_ID, self.sp_data)


    def receive_data_from_dbs(self):
        """Read the sensors and actuators data in DBS"""
        data_num = len(self.DBS_FV_XI_ID)
        result = read_data_from_modbus_device(
            self.ews_client, 
            2 * data_num, 
            self.slave,
            client_name = self.name,
            target_name = 'DBS'
        )
        print('\n', 15*'-----')
        print("> EWS: Read data from DBS: ")
        show_exp_data(self.DBS_FV_XI_ID, result)


    def write_data_to_dbs(self):
        """Write controller command data to DBS"""
        
        print('\n', 15*'-----')
        print("EWS: Write data to DBS: ", self.sp_data)
        sp_register = float32_to_modbus_registers(self.sp_data)
        
        self.store[3].setValues(3, 0, sp_register)


    def write_data_to_plc(self, PLC_ID):
        """Write setpoint data to PLC"""

        PLC_SP_ID, _ = get_data_id(PLC_ID)
        if PLC_ID == 'PLC1':
            PLC_INDEX = 1
            PLC_SP = self.sp_data[1:]

        elif PLC_ID == 'PLC2':
            PLC_INDEX = 2
            PLC_SP = self.sp_data[:1]
        
        # 修改塔顶温度数据
        if PLC_ID == 'PLC1' and self.sim_state == 'A_MITM' and 10 <= self.sim_cnt:
            print('> PLC1 MITM attack simulation: abnormal tower top temperature')
            PLC_SP[0] = 250
                
        EWS_registers = float32_to_modbus_registers(PLC_SP)
        self.store[PLC_INDEX].setValues(3, 0, EWS_registers)
        print('\n', 15*'-----')
        print(f'Write setpoint data to : {PLC_ID}')
        show_exp_data(PLC_SP_ID, PLC_SP)
        print()
        return 0


    def run(self):
        
        interval = self.sim_period / 5
        while True:
            print(10*'**********')
            print(f">>> Simulation condition: {self.sim_state} ")            
            print('\n', 15*'=======')
            print(self.name, "-simulation time：", self.sim_cnt)
            try:
                PLC_interval = self.write_data_to_plc('PLC1')
                time.sleep(interval/2)
                PLC_interval = self.write_data_to_plc('PLC2')
                time.sleep(interval/2)
                    
                self.write_data_to_dbs()
                self.receive_data_from_dbs()
                
                time.sleep(interval)
                self.receive_data_from_his()
                
            except ConnectionException:
                print("EWS: Connection failed, retrying in 5 seconds...")
            
            time.sleep(self.sim_period - 2*interval)
            self.sim_cnt +=1
