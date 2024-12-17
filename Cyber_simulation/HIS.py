
'''
Author: Xin Du
Date: 2023-04-11 22:07:08
LastEditors: Xin Du
LastEditTime: 2024-12-17 11:47:40
Description: Human Interface Station
'''

import time
import random
import pandas as pd
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.modbus import generate_random_floats, float32_to_modbus_registers, decode_float_values, write_data_to_modbus_device, read_data_from_modbus_device
from utils.utils import get_data_id, get_system_state, get_system_config, show_exp_data

class HIS:
    def __init__(self, ip, port, slave, name='HIS'):
        dbs_server_port, ews_server_port, his_client_port = port
        
        self.dbs_client = ModbusTcpClient(host = ip, port=dbs_server_port, source_address=(ip, his_client_port))

        self.ews_client = ModbusTcpClient(host = ip, port=ews_server_port, source_address=(ip, his_client_port+1))

        self.slave = slave
        self.name = name


        self.DBS_SP_ID, self.DBS_FV_XI_ID = get_data_id('DBS')

        sim_cfg = get_system_config('simulation')
        self.sim_period = sim_cfg['sim_period']
        self.sim_state = sim_cfg['sim_state']
        self.sim_cnt = 0

        self.work_condition_df = self.read_work_condition()


    def read_work_condition(self):
        work_condition_file_path = './data/work_condition.csv'
        work_condition = pd.read_csv(work_condition_file_path)
        return work_condition


    def read_data_from_dbs(self):

        work_condition = self.work_condition_df.iloc[self.sim_cnt, :].to_list()
        FV_XI_data_num = len(self.DBS_FV_XI_ID)
        result = read_data_from_modbus_device(
            self.dbs_client,
            2 * FV_XI_data_num,
            self.slave,
            client_name = self.name,
            target_name = 'DBS'
        )
        print('\n', 15*'-----')
        print(f"{self.name}: Read DBS data: ")
        show_exp_data(self.DBS_FV_XI_ID, result)


    def write_data_to_ews(self, interval):
        # sp_data = [6.0 for _ in range(len(self.DBS_SP_ID))]
        work_condition = self.work_condition_df.iloc[self.sim_cnt, :].to_list()
        PLC_SP = work_condition[ : 4]

        # ---- A_FDI  ----
        if self.sim_state== 'A_FDI' and 10 <= self.sim_cnt:

            PLC_SP[0] = 65
            HIS_interval = 2 * 0.7 * interval
            write_data_to_modbus_device(
                self.ews_client,
                PLC_SP,
                self.slave,
                client_name=self.name,
                target_name='EWS'
            )
            time.sleep(HIS_interval)
            write_data_to_modbus_device(
                self.ews_client,
                PLC_SP,
                self.slave,
                client_name=self.name,
                target_name='EWS'
            )
        else:
            HIS_interval = 0
            time.sleep(HIS_interval) 
            write_data_to_modbus_device(
                self.ews_client,
                PLC_SP,
                self.slave,
                client_name = self.name,
                target_name = 'EWS'
            )
        
        print('\n', 15*'-----')
        print(f"{self.name}: Write EWS data: ")
        show_exp_data(self.DBS_SP_ID, PLC_SP)
        
        return HIS_interval


    def run(self):
        
        interval = self.sim_period / 4
        HIS_interval = 0
        while True:
            
            print(10*'**********')
            print(f">>> Simulated operating conditions: {self.sim_state} \n")
            print('\n', 15*'=======')
            print(self.name, "- simulation time：", self.sim_cnt)
            
            try:
                if self.sim_state == 'F_CLF' and 10 <= self.sim_cnt and self.sim_cnt < 60:
                    pass
                else:
                    self.read_data_from_dbs()
                time.sleep(interval)
                # HIS_interval = 0
                HIS_interval = self.write_data_to_ews(interval)

            except ConnectionException:
                print("HIS: Connection failed, retrying in 5 seconds...")
            
            time.sleep(self.sim_period - interval - HIS_interval)

            self.sim_cnt +=1

