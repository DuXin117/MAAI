'''
Author: Xin Du
Date: 2024-11-29 20:52:50
LastEditors: Xin Du
LastEditTime: 2024-12-16 21:09:17
Description: Database Server
'''

import random
import time
import threading
import struct
import sys
import pandas as pd

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.datastore import ModbusServerContext
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.server.sync import StartTcpServer

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.modbus import create_server_context, decode_float_values, run_modbus_server, read_data_from_modbus_device
from utils.utils import get_data_id, get_system_config, show_exp_data, get_time_now

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext


exit_event = threading.Event()

class DBS:
    def __init__(self, ip, port, slave,  name = 'DBS'):
        self.name = name
        self.slave = slave
        # -- 创建DBS客户端 --
        dbs_server_port, ews_server_port, dbs_client_port = port
        print()
        print('> --- Create DBS Modbus TCP client and server ---')
        print(f'> DBS - IP : {ip} - Port : {dbs_server_port}')

        self.ews_client = ModbusTcpClient(ip, port = ews_server_port, source_address = (ip, dbs_client_port))
        
        self.store = create_server_context()
        run_modbus_server(context = self.store, ip = ip, port = dbs_server_port)

        self.XC_SP_id, self.ALL_FV_XI_id = get_data_id('DBS')
        _, self.PLC1_FV_XI_id = get_data_id('PLC1')
        _, self.PLC2_FV_XI_id = get_data_id('PLC2')
        
        base_feature = ['sim_t', 'sim_states']
        process_data_feature = base_feature + self.ALL_FV_XI_id
        self.process_data_pd = pd.DataFrame(columns = process_data_feature)
        date_time = get_time_now('date_time_all')

        sim_cfg = get_system_config('simulation')
        self.sim_state = sim_cfg['sim_state']
        self.sim_period = sim_cfg['sim_period']
        self.sim_data_start_time = sim_cfg['sim_data_start_time']
        self.sim_end_time = sim_cfg['sim_end_time']
        self.sim_cnt = 0
        self.process_data_path = f'./data/physical/FCC_Fractionator_{self.sim_state}_{date_time:s}.csv'


    def read_command_from_EWS(self):
        """Read PLC operation instructions from HIS"""
        
        data_num = len(self.XC_SP_id)
        result = read_data_from_modbus_device(
            self.ews_client, 
            2 * data_num, 
            self.slave,
            client_name = self.name,
            target_name = 'EWS'
        )
        show_exp_data(self.XC_SP_id, result)


    def save_process_data(self, ALL_FV_XI):
        sim_cfg = get_system_config('simulation')
        if self.sim_cnt > 5 and self.sim_cnt < self.sim_end_time:
            
            print(f'----------- sim_time : {self.sim_cnt} ------------')
            process_data = [self.sim_cnt - 5 + self.sim_data_start_time, self.sim_state] + ALL_FV_XI
            process_data_series = pd.Series(process_data, index=self.process_data_pd.columns)
            self.process_data_pd = self.process_data_pd.append(process_data_series, ignore_index=True)
            self.process_data_pd.to_csv(self.process_data_path)
            print('>>> DBS: Process data saved to file <<<\n')


    def read_data_from_plc(self):
        """Read sensor and actuator data from PLC"""
        
        PLC1_result  = self.store[1].getValues(3, 0, 2*len(self.PLC1_FV_XI_id))  # Read data from slave station 1 (PLC1)
        PLC2_result  = self.store[2].getValues(3, 0, 2*len(self.PLC2_FV_XI_id))  # Read data from slave station 1 (PLC2)
        
        ALL_FV_XI_register = PLC1_result + PLC2_result
        
        self.store[3].setValues(3, 0, ALL_FV_XI_register)
        self.store[4].setValues(3, 0, ALL_FV_XI_register)

        # Convert integer data to floating point numbers 
        PLC1_float_data = decode_float_values(PLC1_result)
        PLC2_float_data = decode_float_values(PLC2_result)
        
        # For status order adjustment, refer to device_data_interaction.json
        ALL_FV_XI_data = PLC1_float_data[0 : 3] + PLC2_float_data + PLC1_float_data[3 : ]
        
        print('> ALL_FV_XI_data: ', ALL_FV_XI_data)
        print('> len(ALL_FV_XI_data): ', len(ALL_FV_XI_data))
        
        print('\n', 15*'-----')
        print("\n DBS: Read data from PLC1: ")
        show_exp_data(self.PLC1_FV_XI_id, PLC1_float_data)
        print('\n', 15*'-----')
        print("\n DBS: Read data from PLC2: ")
        show_exp_data(self.PLC2_FV_XI_id, PLC2_float_data)

        self.save_process_data(ALL_FV_XI_data)


    def run(self):
        interval = self.sim_period / 3
        while True:
            print(10*'**********')
            print(f">>> Simulation condition: {self.sim_state} \n")            
            print('\n', 15*'=======')
            print(">>> DBS Running")
            print(self.name, "- simulation time : ", self.sim_cnt)
            try:
                self.read_data_from_plc()
                time.sleep(interval)
                if self.sim_state == 'F_CLF' and 60 <= self.sim_cnt:
                    pass
                else:
                    self.read_command_from_EWS()
            except ConnectionException:
                print("DBS: Connection failed, retrying in 5 seconds...")
            time.sleep(self.sim_period - interval)
            self.sim_cnt +=1

