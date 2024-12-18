'''
Author: Xin Du
Date: 2024-12-11 10:52:26
LastEditors: Xin Du
LastEditTime: 2024-12-18 22:02:51
Description: file content
'''

import copy
import time
import datetime
import numpy as np
import pandas as pd
import config.exp_config as d_cfg

from config.exp_config import exp_group_cfg
from config.model_config import ad_threshold_ratio, al_threshold_ratio
from utils.get_exp_data import get_anomaly_detector_data
from utils.para_process import get_exp_para, get_exp_code, print_model_para
from utils.exp_record import ExpRecord
from model.build_ad_model import ad_metric, build_ad_model
from utils.utils import print_model_result


def cyber_anomaly_detection():
    
    data_type = 'cyber'
    # data_type = 'physical'
    
    exp_type = f'{data_type}_AL'
    test_model_list = ['DNN', 'CNN', 'BILSTM', 'MANN', 'TRAN']

    train_data, test_data, test_labels = get_anomaly_detector_data(domain = data_type)
    
    for model_type in test_model_list:
        
        print(f'\n\n>=========== Model: {model_type} ===========\n')

        # ------ Obtain the parameter dictionary and parameter grid of the experimental model ------
        model_para, grid_para_names, para_grid_list = get_exp_para(model_type)
        
        grid_para_num = len(para_grid_list) - 1
        record = ExpRecord(f'{exp_type}_{model_type}')
        
        for exp_ind, model_para_list in enumerate(para_grid_list):

            # ------- Experimental result record ------
            results = {model_type: {'code': [], 'seed': [], 'ACC': [], 'FAR': [], 'PRE': [], 'REC': [], 'F1': []} for model_type in test_model_list}    

            # ------- Experimental result record ------
            model_train_para = copy.deepcopy(exp_group_cfg['model_train_para'])
            time_start = time.time()
            
            # ------ Loading hyperparameters into the parameter dictionary ------
            for para_ind, para_name in enumerate(grid_para_names):
                
                # ---- Modify model parameters ----
                if para_name in model_para.keys():
                    model_para[para_name] = model_para_list[para_ind]
                    
                # ---- Modify model parameters ----
                elif para_name in model_train_para.keys():
                    model_train_para[para_name] = model_para_list[para_ind]
            
            train_X, test_X  = train_data, test_data
            if 'cyber' in exp_type:
                y_true = test_labels
            elif 'physical' in exp_type:
                y_true = test_labels > 0
                y_true = y_true.astype(int)

            exp_no = f'{exp_ind:0>3d}/{grid_para_num:0>3d}'
            grid_para_info = get_exp_code(grid_para_names, model_para_list)            
            
            print(f'>>> Exp : {exp_no:s}--{grid_para_info:s}')
            
            exp_data = train_X, test_X, y_true
            best_ACC, best_FAR, best_PRE, best_REC, best_F1, ad_seed_list, code_list, ACC_list, FAR_list, PRE_list, REC_list, F1_list = test_ad_model(exp_data, model_type, exp_type, model_para, model_train_para, record, exp_no)
            
            results[model_type]['seed'].extend(ad_seed_list)
            results[model_type]['code'].extend(code_list)
            results[model_type]['ACC'].extend(ACC_list)
            results[model_type]['FAR'].extend(FAR_list)
            results[model_type]['PRE'].extend(PRE_list)
            results[model_type]['REC'].extend(REC_list)
            results[model_type]['F1'].extend(F1_list)            

            time_end = time.time()
            
            # --------- Record of detection statistics under a single seed group ----------
            # Record the current model parameters in CSV
            para_dict = {**model_para, **model_train_para}   
            record.add_ad_record(
                best_ACC   = best_ACC,
                best_FAR   = best_FAR,
                best_PRE   = best_PRE,
                best_REC   = best_REC,
                best_F1    = best_F1,
                mean_ACC   = np.mean(results[model_type]['ACC']),
                mean_FAR   = np.mean(results[model_type]['FAR']),
                model_para = print_model_para(para_dict),
                run_time   = time_end - time_start,
            )

            print('> Time consumption for this round of training: {:.1f} s \n'.format(time_end - time_start))
            
            print_model_result(results)
            print('----'*30, '\n\n')
    


def test_ad_model(exp_data, model_type, exp_type, model_para, model_train_para, record, exp_no):
    ''' Move the detection and evaluation content of the model under different seeds to this function
    '''
    
    train_X, test_X, y_true = exp_data
    seed_list = exp_group_cfg['seed_list']
    if 'ad' in exp_type:
        detect_ratio_list = ad_threshold_ratio[model_type]
    else:
        detect_ratio_list = al_threshold_ratio[model_type]
    ad_seed_list, code_list, ACC_list, FAR_list, PRE_list, REC_list, F1_list = [], [], [], [], [], [], []
    best_ACC, best_FAR = 0, 0

    # ------ Detection and evaluation of models under different seeds -----
    for i, seed in enumerate(seed_list):
        time_start = time.time()
        exp_result = {}
        
        print(f'\n {exp_no} >--------- Seed: {seed} --------\n')
        model = build_ad_model(exp_type, model_type, model_para, model_train_para, seed)
        
        # --------- model training ----------
        model.fit(train_X, y=None)

        y_score, y_label = model.decision_function(test_X, y_true)
            
        if 'AL' in exp_type:
            ratio = 0.98
            train_error = model.eval(train_X)
            # ---- Obtain a list of percentage threshold boundaries for each feature ----
            thresh = np.percentile(train_error, ratio, axis = 0)
            np.set_printoptions(precision=5, suppress=False)
            print('>>> Thresh: ', thresh)


        #-------- Different detection threshold test cycles--------
        # Calculate detection thresholds at different ratios, retaining only results that meet FAR requirements
        for detect_ratio in detect_ratio_list:

            # ---- Anomaly based anomaly localization task ----
            detect_thres = thresh * detect_ratio
            if 'AL' in exp_type:
                if 'physical' in exp_type:
                    y_label = y_label.reshape(-1, 1)
                    y_pred = (y_score >= detect_thres)
                    y_pred = y_pred.reshape(-1, 1)
                
                elif 'cyber' in exp_type:
                    cyber_data_file_path = './data/Combined_cyber_data_1214_20.csv'
                    
                    dataset = pd.read_csv(cyber_data_file_path)
                    device_list = ['DBS', 'EWS', 'HIS',  'PLC1', 'PLC2']
                    
                    virtual_device_ip = {
                        'DBS'  : '192.168.1.2',
                        'EWS'  : '192.168.1.3',
                        'HIS'  : '192.168.1.4',
                        'PLC1' : '192.168.1.5',
                        'PLC2' : '192.168.1.6'
                    }
                    y_pred = (y_score >= detect_thres).astype(int)
                    test_data_num = y_pred.shape[0]
                    # test_data_df = dataset[dataset['sim_t'] > 1000]
                    test_data_df = dataset.iloc[-test_data_num:, :]
                    
                    # Normal communication relationship between different devices
                    normal_comm_pairs = [
                        ('EWS', 'PLC1'), ('EWS', 'PLC2'), ('EWS', 'DBS'), ('DBS', 'HIS'),
                        ('DBS', 'EWS'), ('HIS', 'EWS'), ('PLC1', 'DBS'), ('PLC2', 'DBS')
                    ]

                    al_pred = cyber_domain_detect_anomalies(y_pred, test_data_df, device_list, virtual_device_ip, normal_comm_pairs)
                    y_label = y_label.reshape(-1, 1)
                    y_pred = al_pred.reshape(-1, 1)

            else:
                y_pred = (y_score >= detect_thres).astype(int)
            ACC, FAR, PRE, REC, F1 = ad_metric(y_pred, y_label)
            best_ACC, best_FAR, best_PRE, best_REC, best_F1 = 0, 0, 0, 0, 0
            
            if FAR <= 0.03 and REC > 0.3:

            # Use low false positive rate during anomaly detection
                np.set_printoptions(precision=5, suppress=True)
                print(f'> detect_thres: ', detect_thres)
                ad_seed_list.append(seed)
                code_list.append(0)
                ACC_list.append(ACC)
                FAR_list.append(FAR)
                PRE_list.append(PRE)
                REC_list.append(REC)
                F1_list.append(F1)
                if best_ACC < ACC:
                    best_ACC = ACC
                    best_FAR = FAR
                    best_PRE = PRE
                    best_REC = REC
                    best_F1  = F1

                get_time_now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                
                save_prediction_flag = True
                if 'cyber' in exp_type and save_prediction_flag:
                    al_prediction = y_pred.reshape(-1, 5)
                    np.save(f'./exp_files/prediction/cyber/cyber_detection_prediction_{get_time_now}.npy', al_prediction)
                    
                elif 'physical' in exp_type and save_prediction_flag:
                    al_prediction = y_pred.reshape(-1, 18)
                    np.save(f'./exp_files/prediction/physical/physical_detection_prediction_{get_time_now}.npy', al_prediction)
                break

            elif FAR <= 0.03 and REC < 0.3:
                print('>>> XXXXXXXXXXXX Anomaly localization failed XXXXXXXXXXXX')
                break
            print(f'> Thres_ratio { detect_ratio:.3f} - ACC: {ACC:.4f} FAR: {FAR:.4f} - PRE: {PRE:.3f} - REC: {REC:.3f} - F1: {F1:.3f}')

        print(f'> Thres_ratio { detect_ratio:.3f} - ACC: {ACC:.4f} FAR: {FAR:.4f} - PRE: {PRE:.3f} - REC: {REC:.3f} - F1: {F1:.3f}')

        print(f'> Model : {model_type} - Code : {0} - Seed : {seed} - ACC: {ACC:.3f} - FAR: {FAR:.3f} - PRE: {PRE:.3f} - REC: {REC:.3f} - F1: {F1:.3f}\n')
        
        # --------- Experimental log records under different seeds ----------
        record.add_ad_record(
            seed     = seed,
            best_ACC = ACC,
            best_FAR = FAR,
            best_PRE = PRE,
            best_REC = REC,
            best_F1  = F1,
            run_time = time.time() - time_start,
            detect_ratio = detect_ratio,
        )

    return best_ACC, best_FAR, best_PRE, best_REC, best_F1, ad_seed_list, code_list, ACC_list, FAR_list, PRE_list, REC_list, F1_list


def cyber_domain_detect_anomalies(y_pred, test_data_df, device_list, device_ip, normal_comm_pairs):
    sim_t_list = sorted(test_data_df['sim_t'].unique())  
    anomaly_alerts = np.zeros((len(sim_t_list), len(device_list)), dtype=int)  
    
    # Detecting abnormal devices based on packet reconstruction
    for i, sim_t in enumerate(sim_t_list):
        # Extract all messages of the current sim_t
        sim_t_data = test_data_df[test_data_df['sim_t'] == sim_t]
        bool_index = (test_data_df['sim_t'] == sim_t).values  

        y_pred_sim_t = y_pred[bool_index]        
        # Identify the devices (source and target devices) in the abnormal packet
        for j, pred in enumerate(y_pred_sim_t):
            if pred == 1:  # If the packet is predicted to be abnormal
                sip = sim_t_data.iloc[j]['sip']  # Source IP
                dip = sim_t_data.iloc[j]['dip']  # Destination IP
                # Search for source and destination devices
                for device, ip in device_ip.items():
                    if sip == ip or dip == ip:
                        device_index = device_list.index(device)
                        anomaly_alerts[i, device_index] = 1  # Tag abnormal devices
    
    # Check the continuity of normal communication relationships
    last_appearance = {device: -1 for device in device_list}  # Record the dict of sim_t that appears last for each device
    
    for i, sim_t in enumerate(sim_t_list):
        sim_t_data = test_data_df[test_data_df['sim_t'] == sim_t]
        
        # Check if each normal communication pair appears in the current sim_t
        observed_pairs = set()
        for _, row in sim_t_data.iterrows():
            sip = row['sip']
            dip = row['dip']
            # Search for device name
            src_device = next((dev for dev, ip in device_ip.items() if ip == sip), None)
            dst_device = next((dev for dev, ip in device_ip.items() if ip == dip), None)
            if src_device and dst_device:
                observed_pairs.add((src_device, dst_device))
        
        for pair in normal_comm_pairs:
            src, dst = pair
            if pair not in observed_pairs:
                # If the communication link does not appear for two consecutive sim_t, mark the source device as abnormal
                if last_appearance[src] >= 0 and sim_t - last_appearance[src] > 1:
                    anomaly_alerts[i, device_list.index(src)] = 1
            else:
                last_appearance[src] = sim_t
    
    return anomaly_alerts