
import os
import pandas as pd
import numpy as np
from utils.utils import get_time_now
from config.exp_config import exp_data_cfg
from sklearn.preprocessing import MinMaxScaler



def get_anomaly_detector_data(domain = 'cyber', data_preprocess = True):

    dataset = get_multidomain_data(domain = domain, mode = 'read-csv')

    if domain == 'cyber':
        train_data, test_data, test_label = cyber_data_preprocess(dataset, data_preprocess = data_preprocess)
        
    elif domain == 'physical':
        train_data, test_data, test_label = physical_data_preprocess(dataset)
        
    return train_data, test_data, test_label



def cyber_data_preprocess(dataset, data_preprocess = True):

    if data_preprocess:
        com_data = dataset.copy()
        feature_names = exp_data_cfg['cyber_sim']['feature_names']
        normal_data = com_data[com_data['labels'] == 'NORMAL']
        train_data_num = normal_data.shape[0]
        test_data_num = com_data.shape[0] - train_data_num
        
        # Convert SIP and DIP addresses into sequential numbering
        com_data['sip'] = com_data['sip'].apply(lambda x: int(x.split('.')[-1]) - 2)
        com_data['dip'] = com_data['dip'].apply(lambda x: int(x.split('.')[-1]) - 2)
        
        # Encode sport and dport with serial numbers
        port_order = [5020, 14900, 5021, 15000, 15010, 15011, 15020, 15021, 15030, 15031]
        
        port_mapping = {port: idx for idx, port in enumerate(port_order)}

        com_data['sport'] = com_data['sport'].map(port_mapping)
        com_data['dport'] = com_data['dport'].map(port_mapping)

        labels = com_data['labels']
        sim_states = com_data['sim_states']
        sim_t = com_data['sim_t']
        # Remove unused features
        com_data_without_label = com_data.drop(['sim_t', 'sim_states', 'modbus', 'protoId', 'labels'], axis=1)
        minmax_scaler = MinMaxScaler()
        com_data_normalized_values = minmax_scaler.fit_transform(
            com_data_without_label.values)

        com_data_normalized = pd.DataFrame(com_data_normalized_values, 
        index=com_data_without_label.index, columns=com_data_without_label.columns)

        com_data_normalized['labels'] = labels
        com_data_normalized['sim_states'] = sim_states
        com_data_normalized['sim_t'] = sim_t
        com_data = com_data_normalized
        com_data.to_csv("./data/scaled_com_data.csv")
    else:
        com_data = pd.read_csv("./data/scaled_com_data.csv", index_col = 0)

    train_data = com_data[(com_data['sim_t'] > 0) & (com_data['sim_t'] <= 1000)]
    test_data = com_data[(com_data['sim_t'] > 1000) & (com_data['sim_t'] <= 1700)]
    test_label = com_data.loc[(com_data['sim_t'] >= 1000) & (com_data['sim_t'] < 1700), 'labels']

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

    num_devices = len(device_list)
    num_samples_per_event = 100

    all_labels = np.zeros((0, num_devices), dtype=int)
    event_keys = list(anomaly_event_devices.keys())  
    for event in event_keys:  
        
        anomaly_devices = anomaly_event_devices[event]
        labels = np.zeros((num_samples_per_event, num_devices), dtype=int)
        
        if event in ['F_CF', 'F_CLF']:
            for idx, group in enumerate(anomaly_devices):  
                for device in group:
                    if device in device_list:
                        device_idx = device_list.index(device)
                        labels[idx * 50 : (idx + 1) * 50, device_idx] = 1
        else:
            for device in anomaly_devices:
                if device in device_list:
                    device_idx = device_list.index(device)
                    labels[:, device_idx] = 1

        all_labels = np.vstack((all_labels, labels))

    test_label = all_labels
    
    drop_col_list = ['sim_t', 'sim_states', 'labels', 'sip', 'dip', 'seq', 'ack', 'window', 'transId']
    
    train_data = train_data.drop(drop_col_list, axis=1)
    test_data = test_data.drop(drop_col_list, axis=1)

    print('> train_data', train_data.shape)        
    print('> test_data', test_data.shape)

    return train_data.values, test_data.values, test_label



def physical_data_preprocess(dataset):

    train_data_num = 1000
    test_data_num = 700
    # 读取数据
    minmax_scaler = MinMaxScaler()
    feature_names = exp_data_cfg['FCC_sim']['feature_names']
    
    exp_data_scale = minmax_scaler.fit_transform(dataset[feature_names])
    train_X = exp_data_scale[ : train_data_num, :]
    test_X = exp_data_scale[train_data_num : , :]
    
    labels = dataset['labels'].values
    labels = labels[train_data_num : ]
    al_labels = np.zeros(test_X.shape)
    
    anomaly_states = {
        0: [],
        1: ['FV1', 'TI1', 'PI1'],
        2: ['FV4', 'LI1'],
        3: [],   
        4: ['FI1', 'PI2'],
        5: [], 
        6: [], 
    }
    
    # 将特征名称映射到列索引，以便于后续设置 al_labels
    feature_name_to_index = {name: idx for idx, name in enumerate(feature_names)}

    # 遍历 test_X 中的每一行数据
    for i, label in enumerate(labels):
        # 处理每个状态对应的特征
        if label in anomaly_states:
            # 获取当前状态对应的特征
            anomaly_features = anomaly_states[label]
            for feature in anomaly_features:
                if feature in feature_name_to_index:
                    feature_idx = feature_name_to_index[feature]
                    al_labels[i, feature_idx] = 1  
    
    print('> train_data : ', train_X.shape)        
    print('> test_data : ', test_X.shape)
    print('> al_labels : ', al_labels.shape)

    return train_X, test_X, al_labels



def get_multidomain_data(domain = 'cyber', mode = 're-combine'):
    
    if mode == 're-combine':
        cyber_data_dir = './data/cyber'
        physical_data_dir = './data/physical'
        # Set suitable experimental data areas for each data mode
        mode_config = {
            "NORMAL"   : (   10, 1009),
            "A_MITM"   : ( 1091, 1190),
            "A_FDI"    : ( 1191, 1290),
            "A_DOS"    : ( 1300, 1399),
            "F_SF"     : ( 1403, 1502),
            "F_CLF"    : ( 1502, 1601),
            "F_CF"     : ( 1603, 1702),
            "T_NORMAL" : ( 1702, 1801),
        }
        data_time = get_time_now('date_hour')
        cyber_dataset = Combine_simulation_data(cyber_data_dir, mode_config, f"./data/Combined_cyber_data_{data_time}.csv")
        phy_dataset = Combine_simulation_data(physical_data_dir, mode_config, f"./data/Combined_physical_data_{data_time}.csv")

    elif mode == 'read-csv':
        cyber_data_file_path = './data/Combined_cyber_data_1214_20.csv'
        phy_data_file_path = './data/Combined_physical_data_1214_20.csv'
        cyber_dataset = pd.read_csv(cyber_data_file_path)
        phy_dataset = pd.read_csv(phy_data_file_path)
    
    print('> mode: ', mode)
    print('> domain: ', domain)
    
    if domain == 'cyber':
        return cyber_dataset
    
    elif domain == 'physical':
        return phy_dataset



def Combine_simulation_data(input_dir, mode_config, output_file):
    all_data = []
    new_sim_t_start = 1  
    for mode in mode_config.keys():
        for file_name in os.listdir(input_dir):
            if file_name.endswith('.csv') and mode in file_name:  
                file_path = os.path.join(input_dir, file_name)
                df = pd.read_csv(file_path, index_col=0)
                start, end = mode_config[mode]
                filtered_data = df[(df['sim_t'] >= start) & (df['sim_t'] <= end)].copy()
                labels = list(mode_config.keys()).index(mode)  
                filtered_data['labels'] = labels
                filtered_data['sim_t'] = filtered_data['sim_t'] - start + new_sim_t_start
                new_sim_t_start += end - start + 1
                all_data.append(filtered_data)
                break
    
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data.reset_index(drop=True, inplace=True)
        combined_data.to_csv(output_file, index=False)
        print(f"> Data processing completed, saved to : {output_file} \n")
    else:
        print("> No data files found")

    return combined_data
