
import json
import os
import time
import pandas as pd
from datetime import datetime
from utils.utils import get_data_id


def file_update_time_to_now(file_path):
    current_time = time.time()
    file_update_time = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
    time_difference = current_time - file_update_time
    print(f"FCC Json update Time difference: {time_difference} seconds")
    return time_difference


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


def read_work_condition():
        work_condition_file_path = './data/work_condition.csv'
        work_condition = pd.read_csv(work_condition_file_path)
        return work_condition


def PLC1_control(PI_sensors, SP, errord, sim_cnt):
    
    # --------- 1）Temperature controller at the top of the fractionation tower TC4---------
    delta  = 10 / 3600
    
    _SP_1 = (SP[0] - 32) * (5 / 9) + 273.15
    _SP_2 = (SP[1] - 32) * (5 / 9) + 273.15
    _SP_3 = (SP[2] - 32) * (5 / 9) + 273.15

    UTemp, Ttrack1, Ttrack2 = PI_sensors[0], PI_sensors[1], PI_sensors[2]
    
    print(f'_SP_1: {_SP_1:.4f}, PI_sensors: {PI_sensors[0]:.4f}')
    print(f'_SP_2: {_SP_2:.4f}, PI_sensors: {PI_sensors[1]:.4f}')
    print(f'_SP_3: {_SP_3:.4f}, PI_sensors: {PI_sensors[2]:.4f}')
    
    print()
    
    eTC4   = -1 * ( _SP_1 - UTemp)
    KcTC4  = 4
    TaoTC4 = 0.6 
    V8nom  = 50
    Rliquidbase = 810.630566926004

    if sim_cnt >= 6  :
        V8a = V8nom + KcTC4 * (eTC4 + errord[1] / TaoTC4)
        V8b = max(5, V8a) 
        V8 = min(95, V8b) 
    else:
        eTC4 = 0    
        V8 = V8nom

    ETC4 = eTC4 * delta + errord[1]

    # --------- 2）Temperature controller for the 6th layer tray of the fractionation tower - TC5---------
    p10nom = 100
    KcTC5 = 5  
    TaoTC5 = 1
    eTC5 = (_SP_2 - Ttrack1) * 1

    if sim_cnt >= 6:
        p10a = p10nom + KcTC5 * (eTC5 + errord[2] / TaoTC5)
        p10b = max(10, p10a)
        p10  = min(190, p10b)  
    else:
        eTC5 = 0    
        p10 = p10nom    

    ETC5 = eTC5 * delta + errord[2]
    V10 = p10 * (1 / 2)
    
    # --------- 3）Temperature controller for the 13th layer tray of the fractionation tower - TC6---------
    eTC6 = (_SP_3 - Ttrack2) * 1  
    p11nom = 100
    KcTC6  = 2
    TaoTC6 = 1

    if sim_cnt >= 6:
        p11a = p11nom + KcTC6 * (eTC6 + errord[3] / TaoTC6)
        p11b = max(10 , p11a)
        p11  = min(190, p11b)
        
    else:
        eTC6 = 0
        p11  = p11nom
        
    ETC6 = eTC6 * delta + errord[3]
    V11 = p11   * (1 / 2)
    
    print(20*'----')
    print(f'SP1: {_SP_1:.4f}, UTemp: {UTemp:.4f}, ETC4: {ETC4:.4f}, V8: {V8:.4f}')
    print(f'SP2: {_SP_2:.4f}, Ttrack1: {Ttrack1:.4f}, ETC5: {ETC5:.4f}, V10: {V10:.4f}')
    print(f'SP3: {_SP_3:.4f}, Ttrack2: {Ttrack2:.4f}, ETC6: {ETC6:.4f}, V11: {V11:.4f}')
    print(20*'----')
    
    return V8, V10, V11, ETC4, ETC5, ETC6


def PLC2_control(PI_sensors, SP, errord, sim_cnt):
    # Oil and gas separator liquid level controller

    UMl = PI_sensors
    KcLC2 = 8
    TaoLC2 = 1
    Distillatebase = 810.630566926004 / 0.747045932872508
    delta = 10 / 3600
    V9nom = 50
    
    print(f'> SP: {SP[0]:.4f}')
    
    _SP_0 = SP[0]
    print('_SP_0: ', _SP_0)
    print('UMl: ', UMl)
    eLC2=(_SP_0 - UMl) * (-1);
    
    if sim_cnt >= 6: 
        V9a = V9nom + KcLC2 * (eLC2 + errord[0] / TaoLC2)
        V9b = max(5, V9a)
        V9 = min(95, V9b)
    else:
        eLC2 = 0   
        V9 = V9nom   
    ELC2 = eLC2 * delta + errord[0]
    
    print(20*'----')
    print(f'SP0: {_SP_0:.4f}, UMl: {UMl:.4f}, ELC2: {ELC2:.4f}, V9: {V9:.4f}')
    print(20*'----')
    
    return V9, ELC2 

# ===============================================================================

def write_data_to_actors(actors, MV_SP, name = 'PLC1'):
    Actor_data_file_path = './data/json/actors.json'
   
    if not os.path.exists("./data/json"):
        os.makedirs("./data/json")
    
    current_time = time.time()
    if not os.path.exists(Actor_data_file_path):
        write_json_data = {
            "actors"      : [50.0, 50.0, 50.0, 50.0],
             "MV_SP"      : MV_SP,
             "sim_cnt"    : 0,
             "sim_ready"  : False,
             "last_update": current_time  # 添加仿真启动时间戳
        }
        with open(Actor_data_file_path, "w") as f:
            json.dump(write_json_data, f)
        print("> Created actor.json with initial data")
    else:

        with open(Actor_data_file_path, "r") as f:
            write_json_data = json.load(f)
        if current_time - file_mod_time > 30:
            write_json_data["start_timestamp"] = current_time
            print("> Updated start_timestamp due to file age exceeding 30 seconds")
            sim_cnt = 1
            json_actor = [50.0, 50.0, 50.0, 50.0]
        else:
            json_actor = write_json_data["actors"]

        elapsed_time = current_time - write_json_data.get("start_timestamp", current_time)
        print(f"> Simulation elapsed time: {elapsed_time}")
        write_json_data["sim_cnt"] = int(elapsed_time // 2) + 1
        sim_cnt = write_json_data["sim_cnt"]

        if name == 'PLC1':
            json_actor[1] = actors[1]
            json_actor[2] = actors[2]
            json_actor[3] = actors[3]
            
        elif name == 'PLC2':
            json_actor[0] = actors[0]
            
        write_json_data['MV_SP'] = MV_SP
        with open(Actor_data_file_path, "w") as f:
            json.dump(write_json_data, f)
        print("> Update actor.json")
        
        return sim_cnt


def read_sensors_data(name = 'PLC1'):
    
    sensor_data_file_path = "./data/json/sensors.json"
    if wait_for_update(sensor_data_file_path, timeout=15):
        with open(sensor_data_file_path, "r") as f:
            data = json.load(f)
            json_sensors = data["sensors"]
        print(f"Received data: {sensors}")
        matlab_connect_flag = True
        SP_ID, FV_XI_ID = get_data_id('PLC2', mode = 'XI')
        PLC2_sensors_num = len(FV_XI_ID)
        if name == 'PLC1':
            sensors = json_sensors[PLC2_sensors_num : ]
        elif name == 'PLC2':
            sensors = json_sensors[ : PLC2_sensors_num]
    else:
        print("> Timeout waiting for sensor data.")
        SP_ID, FV_XI_ID = get_data_id(name, mode = 'XI')
        sensors = [0 for _ in range(len(FV_XI_ID))]
        matlab_connect_flag = False
        
    return sensors, matlab_connect_flag

