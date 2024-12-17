'''
Author: Xin Du
Date: 2023-04-13 17:36:37
LastEditors: Xin Du
LastEditTime: 2024-12-17 16:52:16
Description: file content
'''

import random
import struct
import threading
from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext
from pymodbus.server.sync import ModbusTcpServer, StartTcpServer
from pymodbus.datastore import ModbusServerContext

from typing import List, Optional, Union
from utils.utils import get_system_config




def read_data_from_modbus_device(client: ModbusTcpClient, reg_len: int = 20, slave: int = 0, client_name: str = 'client', target_name: str = 'server') -> Optional[List[float]]:

    result = client.read_holding_registers(0, reg_len, unit = slave)
    if result.isError():
        print(f"{client_name}-{slave}: Error reading data from {target_name}")
        return None
    float_data = decode_float_values(result.registers)
    print(f"{client_name}-{slave}: Successfully read data from {target_name}")
    print()
    return float_data



def write_data_to_modbus_device(
    client: ModbusTcpClient, 
    float_values: Optional[List[float]] = None, 
    slave: int = 0, 
    client_name: str = 'client', 
    target_name: str = 'server') -> None:

    if float_values is None:
        float_values = [0.0]

    registers = float32_to_modbus_registers(float_values)
    result = client.write_registers(0, registers, unit=slave)
    if result.isError():
        print(f"{client_name}-{slave}: Error writing data to {target_name}")
    else:
        print(f"{client_name}-{slave}: Successfully wrote data to {target_name}")
        print(">>> Sending data：", float_values)
        print()


def start_tcp_server(context, ip, port):
    server = StartTcpServer(context = context, address=(ip, port))


# Start Modbus Server
def run_modbus_server(context, ip, port):
    server_thread = threading.Thread(target=start_tcp_server, args=(context, ip, port))
    server_thread.start()

def create_slave_context():
    return ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 100),
        co=ModbusSequentialDataBlock(0, [0] * 100),
        hr=ModbusSequentialDataBlock(0, [0] * 100),
        ir=ModbusSequentialDataBlock(0, [0] * 100)
    ) 

def create_server_context():
    store = ModbusServerContext(slaves={
        1: create_slave_context(), # PLC 1
        2: create_slave_context(), # PLC 2
        3: create_slave_context(), # EWS/ DBS 
        4: create_slave_context(), # HIS 
    }, single=False)
    return store


def decode_float_values(input_registers):
    float_data = []
    for i in range(0, len(input_registers), 2):
        float_data.append(struct.unpack(">f", struct.pack(">HH", input_registers[i], input_registers[i+1]))[0])
    return float_data


def float32_to_modbus_registers(float_values):
    registers = []
    for value in float_values:
        packed_value = struct.pack('>f', value)
        register1, register2 = struct.unpack('>HH', packed_value)
        registers.extend([register1, register2])
    return registers


def generate_random_floats(num_values):
    return [random.uniform(0, 10000)/100 for _ in range(num_values)]
