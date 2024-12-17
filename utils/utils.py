'''
Author: Xin Du
Date: 2023-12-02 10:03:32
LastEditors: Xin Du
LastEditTime: 2024-12-17 17:45:52
Description: file content
'''

import datetime
import json
import os
import time
import numpy as np
import pandas as pd

def get_packet_dataset_feature():
    """packet feature acquisition"""

    sim_cfg = get_system_config('parsing')
    base_feature = ['sim_t', 'sim_states']
    data_feature = base_feature + sim_cfg['IP'] + \
        sim_cfg['TCP'] + sim_cfg['MBTCP'] + ['funcCode', 'modbus'] + sim_cfg['DERIVE'] + ['labels']

    return data_feature


last_update_time = time.time()
sim_run_time = 0


def get_sys_sim_time():
    """get simulation time"""
    global last_update_time, sim_run_time
    # Detect changes in system simulation time every second
    current_time = time.time()
    time_diff = current_time - last_update_time

    if time_diff >= 1:
        last_update_time = current_time
        sim_cfg = get_system_config('simulation')
        sim_run_time = sim_cfg['sim_time']
    return sim_run_time



def show_exp_data(data_id_list, data):
    """ Print physical data for display """
    for i, data_id in enumerate(data_id_list):
        print(f'{i}-DATA ID {data_id} : {data[i]:.4f}', )


def get_system_state():
    """ Obtain the current simulation status of the system """
    sim_cfg = get_system_config('simulation')

    return sim_cfg['sim_state']


def get_data_id(device_name, mode = 'FV_XI'):
    """Return the on-site status transmission ID of the device based on its type"""
    
    data_config = get_system_config('data')
    # Control instructions, measured values, and actuator status
    SP_id = data_config[device_name]['SP']
    FV_id = data_config[device_name]['FV']
    XI_id = data_config[device_name]['XI']
    FV_XI_id = FV_id + XI_id
    if mode == 'FV':
        data_id = FV_id
    elif mode == 'XI':
        data_id = XI_id
    elif mode == 'FV_XI':
        data_id = FV_XI_id
        
    return SP_id, data_id


config_json_dir = './config/'

project_config = {
    # Modbus configuration file
    'modbus' : 'modbus_device_config.json',
    # Cyber domain device data interaction configuration file
    'data' : 'cyber_device_data_interaction.json',
    # Packet parsing configuration file
    'parsing' : 'mbtcp_packet_parsing.json',
    # Simulation control configuration file
    'simulation' : 'simulation_control.json',
}


def write_config(config, config_name):
    """Write project configuration file"""
    global config_json_dir, project_config
    config_file_path = config_json_dir + project_config[config_name]
    with open(config_file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


config_cache = {}  # Dictionary for caching configuration
last_read_time = {}  # Dictionary that records the last read time for each configuration

def get_system_config(config_name):
    """Obtain the project configuration file"""

    global config_json_dir, project_config, config_cache, last_read_time
    current_time = time.time()
    # Check if 0.5 seconds have passed since the last read time to avoid conflicts when reading JSON files
    if config_name in last_read_time and current_time - last_read_time[config_name] < 0.1:
        return config_cache[config_name]

    config_file_path = config_json_dir + project_config[config_name]
    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file '{config_file_path}': {e}")
        config = config_cache[config_name]
        
    # Update cache and last read time
    config_cache[config_name] = config
    last_read_time[config_name] = current_time

    return config



def wait_for_update(file_path, timeout = 20):
    """Waiting for file update, timeout is timeout seconds"""
    
    start_time = time.time()
    initial_mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
    wait_time = 0
    while time.time() - start_time < timeout:
        if os.path.exists(file_path) and os.path.getmtime(file_path) > initial_mtime:
            return True
        time.sleep(1)  
        wait_time += 1
        print(f"Waiting for simulation to update results, elapsed time: {wait_time} s ")
    return False


def get_sub_seqs(x_arr, seq_len=100, stride=1):

    seq_starts = np.arange(0, x_arr.shape[0] - seq_len + 1, stride)
    x_seqs = np.array([x_arr[i:i + seq_len] for i in seq_starts])

    return x_seqs


def get_sub_seqs_label(y, seq_len=100, stride=1):

    seq_starts = np.arange(0, y.shape[0] - seq_len + 1, stride)
    ys = np.array([y[i:i + seq_len] for i in seq_starts])
    y = np.sum(ys, axis=1) / seq_len

    y_binary = np.zeros_like(y)
    y_binary[np.where(y!=0)[0]] = 1
    return y_binary



def get_time_now(time_mode = 'date_time_all'):
    '''Obtain system time in multiple formats''' 

    local_time = datetime.datetime.now().strftime('%H%M%S')
    local_date = datetime.datetime.now().strftime('%m%d')
    if time_mode == 'date_time_all': 
        return f'{local_date:s}_{local_time:s}'
    elif time_mode == 'date':
        return f'{local_date:s}'
    elif time_mode == 'date_hour':
        local_hour = local_time = datetime.datetime.now().strftime('%H')
        return f'{local_date:s}_{local_hour:s}'
    elif time_mode == 'hm_time':
        hm_time = datetime.datetime.now().strftime('%H%M')
        return f'{hm_time:s}'
    elif time_mode == 'h:m:s':
        return datetime.datetime.now().strftime('%H:%M:%S')
    else:
        return f'{local_time:s}'



def print_model_result(results):
    '''Print the comprehensive detection results of the DL model
    '''
    print()
    for model_type, values in results.items():
        seed_list = values['seed']
        code_list = values['code']
        acc_stats = values['ACC']
        far_stats = values['FAR']
        pre_stats = values['PRE']
        rec_stats = values['REC']
        f1_stats  = values['F1']

        # Initialize dictionary classified by code
        code_stats = {code: {'seed': [], 'ACC': [], 'FAR': [], 'PRE': [], 'REC': [], 'F1': []} for code in set(code_list)}
        
        # Assign the results to each code
        for i in range(len(acc_stats)):
            seed = seed_list[i]
            code = code_list[i]
            acc = acc_stats[i]
            far = far_stats[i]
            pre = pre_stats[i]
            rec = rec_stats[i]
            f1  = f1_stats[i]
            
            code_stats[code]['seed'].append(seed)
            code_stats[code]['ACC'].append(acc)
            code_stats[code]['FAR'].append(far)
            code_stats[code]['PRE'].append(pre)
            code_stats[code]['REC'].append(rec)
            code_stats[code]['F1'].append(f1)

        print(f'\n>=========== Stats: {model_type} ===========<')
        sorted_codes = sorted(code_stats.keys(), key=lambda x: int(x))

        # Print statistical data for each code separately
        for code in sorted_codes:
            stats = code_stats[code]
            seed_list = stats['seed']
            acc_list = stats['ACC']
            far_list = stats['FAR']
            pre_list = stats['PRE']
            rec_list = stats['REC']
            f1_list  = stats['F1']

            print(f'\n------- Code: {code} Stats -------')
            print("| Seed |   ACC   |   FAR   |   PRE   |   REC   |   F1    |")
            print("|------|---------|---------|---------|---------|---------|")
            
            # Print experimental data for each seed
            for i in range(len(acc_list)):
                print(f"|  {seed_list[i]:2d}  | {acc_list[i]:0.3f}   | {far_list[i]:0.3f}   | {pre_list[i]:0.3f}   | {rec_list[i]:0.3f}   | {f1_list[i]:0.3f}   |")
            
            print()
            
            # Print information such as the average and standard deviation of the current code
            if acc_list:  
                print(f'ACC Average: {np.mean(acc_list):.4f}')
                print(f'ACC Std: {np.std(acc_list):.4f}')
                print(f'ACC Min: {np.min(acc_list):.4f}')
                print(f'ACC Max: {np.max(acc_list):.4f}')
                print()
                print(f'FAR Average: {np.mean(far_list):.4f}')
            else:
                print(f'No valid results for code {code}.')
