'''
Author: Xin Du
Date: 2023-04-12 11:49:00
LastEditors: Xin Du
LastEditTime: 2024-12-17 10:58:04
Description: Security analysis host
'''
import time
import pandas as pd

from scapy.utils import wrpcap
from pymodbus.constants import Defaults
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.utilities import hexlify_packets
from io import BytesIO
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.packet_parsing import modbus_packet_parsing
from utils.utils import get_sys_sim_time, get_packet_dataset_feature, get_system_config, get_system_state

from scapy.all import *
from scapy.contrib.modbus import ModbusADURequest, ModbusADUResponse


class SAH:
    
    def __init__(self, interface=None):
        self.interface = interface
        self.captured_packets = []
        self.parsed_data = []
        self.sys_time = time.time()
        self.sim_time = 0
        
        columns = get_packet_dataset_feature()
        self.dataset = pd.DataFrame(columns = columns)
        self.data_file_path = 'dataset'
        self.data_cnt = 0

        # Read simulation configuration
        sim_cfg = get_system_config('simulation')
        sim_cdn_cfg = get_system_config('condition')
        self.sim_end_time = sim_cfg['sim_end_time']
        self.sim_data_start_time = sim_cfg['sim_data_start_time']
        self.sim_state = sim_cfg['sim_state']
        
        sim_period = sim_cfg['sim_period']
        self.real_sim_time_out = self.sim_end_time * sim_period + 50
        self.sim_state_list = sim_cdn_cfg['sim_state_list']
        self.stop_sniffing = False
        self.sim_data_start_time = sim_cfg['sim_data_start_time']


    def add_data_to_dataset(self, parsed_data):
        """Add communication traffic to the DataFrame data"""
        data_series = pd.Series(parsed_data, index=self.dataset.columns)
        self.dataset = self.dataset.append(data_series, ignore_index=True)
        self.data_cnt +=1
        print('>>> ---- Data : ', self.data_cnt, ' ---- ')


    def process_packet(self, packet):
        """Communication packet processing"""
        
        sim_time = get_sys_sim_time()
        if sim_time > 5:
            self.captured_packets.append(packet)
            start_time = time.time()
            print('-----------Deep package parsing ------------')
            parsed_data = modbus_packet_parsing(packet)
            
            # self.parsed_data.append(parsed_data)
            self.parsed_data = [self.sim_data_start_time + sim_time - 5, self.sim_state] + parsed_data
            if len(self.parsed_data) > 2:
                self.add_data_to_dataset(self.parsed_data)
            end_time = time.time()
            print(f"> modbus_packet_parsing execution time: {end_time - start_time:.4f} s \n")        
            
        elif sim_time > self.sim_end_time:
            self.stop_sniffing = True
            

    def sniff_online_packet(self):
        """Sniffing online packet"""
        
        modbus_cfg = get_system_config('modbus')
        sim_cfg = get_system_config('simulation')
        DBS_server_port = modbus_cfg['DBS']['server_port']
        EWS_server_port = modbus_cfg['EWS']['server_port']
        save_sim_file_flag = sim_cfg['save_sim_file']
        packet_filter = f"tcp and (port {DBS_server_port} or port {EWS_server_port})"

        sniff(
            iface  = '\\Device\\NPF_Loopback', 
            filter = packet_filter, 
            store  = False, 
            stop_filter = lambda x: self.stop_sniffing,
            prn    = self.process_packet, 
            timeout = self.real_sim_time_out
        )

        if save_sim_file_flag :
            # Save the captured data packet to a PCAP file
            now = datetime.now()
            date_string = now.strftime("%Y%m%d_%H")
            packet_output_file = f'./data/ModbusTCP_{date_string}.pcap'
            wrpcap(packet_output_file, self.captured_packets)
            print(f'>>> Saved captured packets to {packet_output_file}')

            # Save the captured data packet to a CSV file
            data_file_path = f'./data/cyber/ModbusTCP_{self.sim_state}_{date_string}.csv'
            self.dataset.to_csv(data_file_path)
            print(f'>>> Saved dataset to {data_file_path}')


    def run(self):
    
        self.sniff_online_packet()





