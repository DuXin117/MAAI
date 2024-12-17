
'''
Author: Xin Du
Date: 2024-11-20 10:04:49
LastEditors: Xin Du
LastEditTime: 2024-12-17 15:36:12
Description: cyber domain simulation
'''

import time
import win32gui
import win32con
import subprocess

from utils.utils import get_system_config, write_config


def run_script(script_name, device_name):
    """Run device script"""
    cmd = f'start "{device_name}" cmd.exe /k python {script_name} {device_name}'
    return subprocess.Popen(cmd, shell=True)


def enum_windows_callback(hwnd, window_list):
    """List open cmd windows"""
    if win32gui.IsWindowVisible(hwnd):
        window_list.append(hwnd)


def close_cmd_window(cmd_key = '.py'):
    """Close the win window containing a specific name"""

    print('>>> Close all open cmd windows')
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)

    for hwnd in windows:
        class_name = win32gui.GetClassName(hwnd)
        window_text = win32gui.GetWindowText(hwnd)
        if class_name == 'ConsoleWindowClass' and cmd_key in window_text:
            if 'SAH' in window_text:
                pass
            else:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                print(">>> close Window：", window_text)


def system_startup():
    device_list = ['SAH', 'EWS', 'DBS',  'HIS',  'PLC1', 'PLC2']
    for device_name in device_list:
        if device_name == 'SAH':
            _ = run_script('./Cyber_simulation/run_device.py', device_name)
            time.sleep(6)
        else:
            _ = run_script('./Cyber_simulation/run_device.py', device_name)


if __name__ == "__main__":

    print(">>> Start the simulation system and run scripts for each device")
    mode_config = {
        "NORMAL": {
            'sim_data_start_time': 0,
            'sim_end_time': 1200
        },
        "A_MITM": {
            'sim_data_start_time': 1080,
            'sim_end_time': 130
        },
        "A_FDI": {
            'sim_data_start_time': 1180,
            'sim_end_time': 130
        },
        "A_DOS": {
            'sim_data_start_time': 1290,
            'sim_end_time': 120
        },
        "F_SF": {
            'sim_data_start_time': 1400,
            'sim_end_time': 130
        },
        "F_CLF": {
            'sim_data_start_time': 1500,
            'sim_end_time': 110
        },
        "F_CF": {
            'sim_data_start_time': 1600,
            'sim_end_time': 110
        },
        "T_NORMAL": {
            'sim_data_start_time': 1700,
            'sim_end_time': 110
        }
    }
    
    # Testing of various simulation models
    sim_state = "NORMAL"
    # sim_state = "T_NORMAL"
    # sim_state = "A_MITM"
    # sim_state = "A_FDI"
    # sim_state = "A_DOS"
    # sim_state = "F_SF"
    # sim_state = "F_CLF"
    # sim_state = "F_CF"

    sim_cfg = get_system_config('simulation')
    sim_cfg['sim_state'] = sim_state
    sim_cfg['sim_time'] = 0
    sim_cfg['sim_data_start_time'] = mode_config[sim_state]['sim_data_start_time']
    sim_cfg['sim_end_time'] = mode_config[sim_state]['sim_end_time']
    write_config(sim_cfg, 'simulation')
    sim_end_time = sim_cfg['sim_end_time']
    
    print(f">>> Simulation system startup, simulation mode:{sim_state} <<<")
    system_startup()
    sim_period = 2
    sim_time = sim_cfg['sim_time']
    
    while sim_time < sim_end_time:
        
        print(f">>> -------- sim_time: {sim_time} ---------")

        try:
            sim_cfg = get_system_config('simulation')
        except:
            print(f">>> Simulation system configuration file read failed, please check the simulation system configuration file")

        sim_time = sim_cfg['sim_time']
        time.sleep(2)
        
    print()
    close_cmd_window('.py')
    