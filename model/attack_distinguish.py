'''
Author: Xin Du
Date: 2023-05-12 16:54:09
LastEditors: Xin Du
LastEditTime: 2024-12-19 15:19:43
Description: Attack fault identification module
'''

import ast
import numpy as np
import pandas as pd

from config.exp_config import exp_data_cfg
from model.risk_assessment import AttackRisAssessment
from sklearn.metrics import accuracy_score, precision_score, f1_score, recall_score, confusion_matrix


def improve_attack_intention_evaluation(cp_alarms_list):

    attack_intention_list = []
    ARA = AttackRisAssessment()
    criticality_score = set_phy_device_criticality()
    for cp_alarms in cp_alarms_list:
        
        if cp_alarms == []:
            attack_intention_list.append(0)
            continue

        fault_similarity = fault_similarity_evaluate(cp_alarms)
        ar_evidence = ARA.get_ad_evidence(cp_alarms)
        attack_risk = ARA.perform_inference(ar_evidence, criticality_score)

        attack_intention = attack_risk * (1 - fault_similarity)

        attack_intention_list.append(attack_intention)

    return attack_intention_list



def set_phy_device_criticality():

    device_criticality = {
        'H': ["FV1", "FV2", "FV3", "FV4"],
        # 回路传感器
        'M': ['LI1', 'TI1', 'TI2', 'TI3']
    }
    criticality = [2, 1, 0.5]
    phy_device_list = exp_data_cfg['FCC_sim']['feature_names']
    criticality_score = {}
    for device in phy_device_list:
        if device in device_criticality['H']:
            criticality_score[device] = criticality[0]
        elif device in device_criticality['M']:
            criticality_score[device] = criticality[1]
        else:
            criticality_score[device] = criticality[2]    

    return criticality_score



def improve_attack_intention_evaluation_test():
    ar_result_list = []
    ARA = AttackRisAssessment()
    criticality_score = set_phy_device_criticality()
    # 生成攻击故障报警列表
    cp_alarm_list = generate_attack_fault_alarm_list()
    print('> cp_alarm_list: ', cp_alarm_list)
    print('\n')

    for alarm_type, alarm_set_list in cp_alarm_list.items():
        
        print(f'> ===== alarm_type: {alarm_type} =====')

        for i, alarm_list in enumerate(alarm_set_list):
            print(f'* {alarm_type}-{i+1}')
            print('  * alarm_list: ', alarm_list)

            fault_similarity = fault_similarity_evaluate(alarm_list)

            ar_evidence = ARA.get_ad_evidence(alarm_list)
            
            attack_prob = ARA.perform_inference(ar_evidence, criticality_score)
            
            ar_result_list.append(attack_prob)
            print(f'  * Fault dissimilarity: {1 - fault_similarity:.4f}')
            print(f'  * Attack probability: {attack_prob:.4f}')
            print(f'  * Attack intention: {attack_prob * (1 - fault_similarity):.4f}')
            print('\n')
        print('\n')


def fault_similarity_test():
    
    ar_result_list = []

    cp_alarm_list = generate_attack_fault_alarm_list()

    print('> cp_alarm_list: ', cp_alarm_list)
    print('\n')
    for alarm_type, alarm_set_list in cp_alarm_list.items():
        print(f'> ===== alarm_type: {alarm_type} =====')
        for alarm_list in alarm_set_list:
            print('> alarm_list: ', alarm_list)
            fault_similarity = fault_similarity_evaluate(alarm_list)
            print('> Fault similarity: ', fault_similarity)
            print('\n')
        print('\n')


def fault_similarity_evaluate(device_list):

    max_fault_devices = 10
    # randomness_coef = 1 / (max_fault_devices - 1)
    randomness_coef = 0.9
    local_coef = 0.4
    supervisory_layer = ['HIS', 'DBS', 'EWS']
    control_layer = ['PLC1', 'PLC2', 'PLC3']
    alarm_layers_set = set()
    alarm_num = len(device_list)

    for device in device_list:
        if device in supervisory_layer:
            alarm_layers_set.add('supervisory_layer')
        elif device in control_layer:
            alarm_layers_set.add('control_layer')
        else:
            alarm_layers_set.add('physical_layer')
    alarm_layers_num = len(alarm_layers_set)
    local_character = 1 - local_coef * (alarm_layers_num - 1)
    randomness = randomness_coef ** (alarm_num)

    return local_character * randomness



def generate_attack_fault_alarm_list():

    alarm_list = {

        'MITM' : [
            ['EWS', 'PLC1', 'FV3', 'TI3' , 'FI4']
        ],
        'FDI' : [
            ['HIS', 'EWS', 'PLC2', 'FV4', 'LI1' ]
        ],
        'DoS' : [
            ['EWS', 'PLC2', 'FV4', 'LI1', 'FI1', 'FI2' ]
        ],
        'SF': [

            ['FI1'], 
            ['PI2'], 

        ],
        'CLF': [
            ['EWS'],  
            ['DBS'],  
        ],
        'CF': [
            ["FV1", "FV2", "FV3", "TI1", "TI2", "TI3", "TI4", "FI3", "FI4", "FI5", "FI6", "PI1", "PI2", "LI2"],
            ["FV4", "FI1", "LI1", "FI2"],
        ]
    }

    return alarm_list


def map_labels(label):
    if 1 <= label <= 3:
        return 1
    elif 4 <= label <= 6:
        return 2
    else:
        return label 


def anomaly_detect_metric(predict, labels, setting = '', mode = 'simple'):

    binary_labels = labels > 0

    all_accuracy = accuracy_score(binary_labels, predict)
    all_precision = precision_score(binary_labels, predict, average = 'binary')
    all_recall = recall_score(binary_labels, predict)
    all_f1 = f1_score(binary_labels, predict)
    
    data_labels = [0, 1]
    cm = confusion_matrix(binary_labels, predict, labels=data_labels)
    TP, TN, FP, FN = cm[1][1] , cm[0][0] , cm[0][1], cm[1][0]
    false_alarm = FP / (FP + TN)

    print('> Thres ', setting, f'-ACC: {all_accuracy:.4f} FAR: {false_alarm:.4f}--Precision: {all_precision:.4f}--Recall: {all_recall:.4f}--F1: {all_f1:.4f}')


    if mode == 'complex':
        precision_scores = []
        anomaly_type = ['NORMAL', 'A_MITM', 'A_FDI', 'A_DOS', 'F_SF', 'F_CLF', 'F_CF']

        compare_label  = [1, 2, 3, 5]
        
        for i in compare_label:

            binary_labels = (labels == i) | (labels == 0)  
            binary_predict = predict[binary_labels]  
            binary_labels = labels[binary_labels] == i  

            print(f'>Label {i}: ', sum(labels == i))
            print(f'>Label 0: ', sum(labels == 0))

            precision = precision_score(binary_labels, binary_predict, average='binary')
            recall = recall_score(binary_labels, binary_predict)
            precision_scores.append(precision)

            print(f"> Abnormal event type {i}:", anomaly_type[i])
            print(f"Precision: {precision}")
            print(f"Recall: {recall}")
            print("-" * 30)

    return all_accuracy, false_alarm, all_precision, all_recall, all_f1


