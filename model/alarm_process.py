'''
Author: Xin Du
Date: 2024-09-18 16:32:26
LastEditors: Xin Du
LastEditTime: 2024-12-19 21:40:17
Description: Multi domain alarm processing
'''
import os
import ast
import copy
import pandas as pd
import numpy as np
from config.bn_config import cyb_devices, phy_devices
from utils.anomaly_detect import anomaly_detect_metric, afi_metric
from model.alarm_filter import Spatiotemporal_alarm_filter, alarm_topology_filter
from model.attack_distinguish import improve_attack_intention_evaluation
from utils.utils import get_time_now


def get_cyber_physical_alarms(cyber_anomaly_predict_file, physical_anomaly_predict_file):

    cyber_prediction = np.load(cyber_anomaly_predict_file)
    physical_prediction = np.load(physical_anomaly_predict_file)
    cyb_device_list = ['DBS', 'EWS', 'HIS',  'PLC1', 'PLC2']
    phy_device_list = ['FV1', 'FV2', 'FV3', 'FV4', 'TI1', 'TI2', 'TI3', 'TI4', 'FI1', 'FI2', 'FI3', 'FI4', 'FI5', 'FI6', 'PI1', 'PI2', 'LI1', 'LI2']
    cyber_physical_alarms = []
    cyber_alarms_list = []
    physical_alarms_list = []
    test_t_num = cyber_prediction.shape[0]

    # Traverse each time step, combining network and physical anomaly information
    for t in range(test_t_num):
        current_cyber_alerts = cyber_prediction[t]  
        current_physical_alerts = physical_prediction[t]  

        cyber_alert_devices = [cyb_device_list[i] for i, alert in enumerate(current_cyber_alerts) if alert == 1]
        physical_alert_devices = [phy_device_list[i] for i, alert in enumerate(current_physical_alerts) if alert == 1]
                
        combined_alerts = cyber_alert_devices + physical_alert_devices
        cyber_alarms_list.append(cyber_alert_devices)
        physical_alarms_list.append(physical_alert_devices)
        cyber_physical_alarms.append(combined_alerts)

    return cyber_physical_alarms, cyber_alarms_list, physical_alarms_list



def multidomain_alarm_process():

    cyber_folder = r'exp_files\prediction\cyber'
    physical_folder = r'exp_files\prediction\physical'

    # Retrieve the list of. npy files in the cyber and physical folder
    cyber_npy_files = [os.path.join(cyber_folder, file) for file in os.listdir(cyber_folder) if file.endswith('.npy')]

    physical_npy_files = [os.path.join(physical_folder, file) for file in os.listdir(physical_folder) if file.endswith('.npy')]    
    
    for i in range(7):
        
        print('\n\n\n')
        print(25*'-----')
        print(f'---------- test {i} ----------')
        cyber_prediction = np.load(cyber_npy_files[i])
        physical_prediction = np.load(physical_npy_files[i])

        filter_mode_list = ['window', 'topology','window_topology']
        cp_alarms, cyb_alarms, phy_alarms = get_cyber_physical_alarms(cyber_npy_files[i], physical_npy_files[i])

        for filter_mode in filter_mode_list:

            print('\n -------------------------------------------------------')
            print(f"Processing with filter_mode '{filter_mode}'")
            filtered_cyb_alarms_list, filtered_phy_alarms_list = Spatiotemporal_alarm_filter(cp_alarms, filter_mode = filter_mode)
            
            anomaly_location_evaluation(cyb_alarms, phy_alarms, filtered_cyb_alarms_list, filtered_phy_alarms_list)
            
            anomaly_identification_evaluation(copy.deepcopy(cp_alarms), copy.deepcopy(filtered_cyb_alarms_list), copy.deepcopy(filtered_phy_alarms_list))

            

def assign_afi_label(x):
    if x['labels'] in [0, 7]:
        return 0
    elif x['labels'] in range(1, 4):
        return 1
    elif x['labels'] in range(4, 7):
        return 2
    else:
        return x['labels'] 


def anomaly_identification_evaluation(cp_alarms, filtered_cyb_alarms, filtered_phy_alarms):
    
    alarm_num = len(cp_alarms)
    filtered_cp_alarms = []
    for t in range(alarm_num):
        filtered_cp_alarms.append(filtered_cyb_alarms[t] + filtered_phy_alarms[t])
    
    for sub_list in cp_alarms[200: 300]:
        sub_list.extend(['FI1', 'LI1', 'FI2', 'FV4'])
    for sub_list in filtered_cp_alarms[200: 300]:
        sub_list.extend(['FI1', 'LI1', 'FI2', 'FV4'])
    
    filtered_attack_intention = improve_attack_intention_evaluation(filtered_cp_alarms)
    attack_intention = improve_attack_intention_evaluation(cp_alarms)
   
    phy_dataset = pd.read_csv('./data/Combined_physical_data_1214_20.csv')
    
    test_phy_data = phy_dataset[phy_dataset['sim_t'] > 1000]
    test_phy_data.loc[:, 'cps_alarms'] = cp_alarms
    test_phy_data.loc[:, 'filtered_cps_alarms'] = filtered_cp_alarms
    test_phy_data.loc[:, 'afi_labels'] = test_phy_data.apply(assign_afi_label, axis=1)
    test_phy_data.loc[:, 'filtered_attack_intention'] = filtered_attack_intention
    test_phy_data.loc[:,'attack_intention'] = attack_intention

    attack_threshold = 0.60

    filtered_afi_prediction = test_phy_data['filtered_attack_intention'].apply(lambda x: 0 if x == 0 else 2 if 0 < x and x < attack_threshold else 1)
    afi_prediction = test_phy_data['attack_intention'].apply(lambda x: 0 if x == 0 else 2 if 0 < x and x < attack_threshold else 1)

    test_phy_data.loc[:, 'filtered_afi_predict'] = filtered_afi_prediction
    test_phy_data.loc[:, 'afi_predict'] = afi_prediction

    afi_labels = test_phy_data['afi_labels']

    print('\n')
    print('======================= Anomaly localization result ======================')
    print(' Accuracy of attack identification for unfiltered alarms ')
    afi_metric(afi_prediction, afi_labels)
    print(' Accuracy of attack identification for filtered alarms ')
    afi_metric(filtered_afi_prediction, afi_labels)
    test_phy_data.to_csv('./exp_files/test_phy_data_result.csv', index=False)

    return test_phy_data


def anomaly_location_evaluation(cyb_alarms_list, phy_alarms_list, filtered_cyb_alarms_list, filtered_phy_alarms_list):
    
    cyb_alarm_label_list, phy_alarm_label_list = add_cp_alarms_labels()
    cyb_devices_num = 5
    phy_devices_num = 18

    alarm_label_num = len(cyb_alarm_label_list)

    cyb_alarm_label_array = np.zeros((alarm_label_num, cyb_devices_num))
    phy_alarm_label_array = np.zeros((alarm_label_num, phy_devices_num))
    
    cyb_alarm_array = np.zeros((alarm_label_num, cyb_devices_num))
    phy_alarm_array = np.zeros((alarm_label_num, phy_devices_num))
    
    filtered_cyb_alarm_array = np.zeros((alarm_label_num, cyb_devices_num))
    filtered_phy_alarm_array = np.zeros((alarm_label_num, phy_devices_num))

    for i in range(alarm_label_num):
        cyb_alarms_label = cyb_alarm_label_list[i]
        phy_alarms_label = phy_alarm_label_list[i]
        filtered_cyb_alarms = filtered_cyb_alarms_list[i]
        filtered_phy_alarms = filtered_phy_alarms_list[i]
        cyb_alarms = cyb_alarms_list[i]
        phy_alarms = phy_alarms_list[i]

        if len(cyb_alarms_label) > 0:
            for cyb_alarm in cyb_alarms_label:
                cyb_alarm_label_array[i][cyb_devices.index(cyb_alarm)] = 1
        if len(phy_alarms_label) > 0:
            for phy_alarm_label in phy_alarms_label:
                phy_alarm_label_array[i][phy_devices.index(phy_alarm_label)] = 1
        
        if len(filtered_cyb_alarms) > 0:
            for filtered_cyb_alarm in filtered_cyb_alarms:
                filtered_cyb_alarm_array[i][cyb_devices.index(filtered_cyb_alarm)] = 1
        if len(filtered_phy_alarms) > 0:
            for filtered_phy_alarm in filtered_phy_alarms:
                filtered_phy_alarm_array[i][phy_devices.index(filtered_phy_alarm)] = 1

        if len(cyb_alarms) > 0:
            for cyb_alarm in cyb_alarms:
                cyb_alarm_array[i][cyb_devices.index(cyb_alarm)] = 1
        if len(phy_alarms) > 0:
            for phy_alarm in phy_alarms:
                phy_alarm_array[i][phy_devices.index(phy_alarm)] = 1
    # ---------------------------------------------
    cyb_alarm_label_array = cyb_alarm_label_array.flatten()
    phy_alarm_label_array = phy_alarm_label_array.flatten()
    cyb_alarm_array = cyb_alarm_array.flatten()
    phy_alarm_array = phy_alarm_array.flatten()
    filtered_cyb_alarm_array = filtered_cyb_alarm_array.flatten()
    filtered_phy_alarm_array = filtered_phy_alarm_array.flatten()
    
    print('======================= Anomaly localiztion result ======================')
    print('-------- Unfiltered alarm data --------')
    print('* Accuracy of Cyber Domain Alarm Localization ')
    anomaly_detect_metric(cyb_alarm_array, cyb_alarm_label_array)
    print('* Accuracy of Physical Domain Alarm Localization ')
    anomaly_detect_metric(phy_alarm_array, phy_alarm_label_array)
    
    print('\n')
    print('--------- filtered alarm data ---------')
    print('* Accuracy of Cyber Domain Alarm Localization ')
    anomaly_detect_metric(filtered_cyb_alarm_array, cyb_alarm_label_array)
    print('* Accuracy of Physical Domain Alarm Localization ')
    anomaly_detect_metric(filtered_phy_alarm_array, phy_alarm_label_array)


def add_cp_alarms_labels(ad_result = None):
    """ Add positioning labels to multi domain alert data
    """
    cyb_alarm_label_list = []
    phy_alarm_label_list = []

    device_list = ['DBS', 'EWS', 'HIS',  'PLC1', 'PLC2']
    anomaly_event_devices = {
        'A_MITM': ['EWS', 'PLC1'],
        'A_FDI': ['HIS', 'EWS', 'PLC2'],
        'A_DOS': ['EWS', 'PLC2'],
        'F_SF': [],
        'F_CLF': [['EWS'], ['DBS']],  
        'F_CF': [['PLC1'], ['PLC2']], 
        'T_NORMAL': [],
    }
    cyb_alarm_label_list = [['EWS', 'PLC1']] * 100 + [['HIS', 'PLC2']] * 100 + [['EWS', 'PLC2']] * 100 + [[]] * 100 + [['EWS']] * 50 + [['DBS']] * 50 + [['PLC1']] * 50 + [['PLC2']] * 50 + [[]] * 100

    phy_alarm_label_list = [['FV1', 'FV4', 'TI2']] * 100 + [['FV4', 'LI1']] * 100 + [[]] * 100 + [['FI1']] * 50 + [['PI2']] * 50 + [[]] * 100  + [[]] * 100 + [[]] * 100

    return cyb_alarm_label_list, phy_alarm_label_list

