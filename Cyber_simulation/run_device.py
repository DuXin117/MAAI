'''
Author: Xin Du
Date: 2024-11-28 21:21:34
LastEditors: Xin Du
LastEditTime: 2024-12-06 20:10:16
Description: file content
'''

import sys
import time
import random
import json
from PLC import PLC
from DBS import DBS
from EWS import EWS
from HIS import HIS
from SAH import SAH
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.utils import get_system_config

def get_device_modbus_param(device_name='PLC1'):
    """Read the IP and port of Modbus devices"""

    if device_name == 'SAH':
        return None, None, None
    else:
        config = get_system_config('modbus')
        HOST_IP = config[device_name]['host_ip']
        DBS_SERVER_PORT = config['DBS']['server_port']
        EWS_SERVER_PORT = config['EWS']['server_port']
        CLIENT_PORT = config[device_name]['client_port']
        MIX_PORT = (DBS_SERVER_PORT, EWS_SERVER_PORT, CLIENT_PORT)
        SLAVE = config[device_name]['slave']

        return HOST_IP, MIX_PORT, SLAVE



def modbus_device_start(device_name = 'PLC1'):
    """启动modbus设备仿真"""

    HOST_IP, PORT, SLAVE = get_device_modbus_param(device_name)
    device_classes = {
        'DBS' : DBS,
        'EWS': EWS,
        'HIS': HIS,
        'SAH': SAH,
    }
    
    for i in range(1, 3):
        device_classes[f'PLC{i}'] = PLC
    
    if device_name in device_classes:
        DeviceClass = device_classes[device_name]
        if device_name == 'SAH':
            device = DeviceClass(None)
        else:
            device = DeviceClass(HOST_IP, PORT, SLAVE, name = device_name)
    else:
        raise ValueError(f">>> Unknown device name: {device_name}")

    time.sleep(random.random())    
    device.run()


if __name__ == '__main__':
    device_name = sys.argv[1:][0]
    print('>>> start device: ', device_name)
    modbus_device_start(device_name)


