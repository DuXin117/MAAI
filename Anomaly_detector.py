'''
Author: Xin Du
Date: 2024-12-09 14:48:29
LastEditors: Xin Du
LastEditTime: 2024-12-15 12:58:48
Description: multi-domain anomaly detector
'''

from model.multidomain_anomaly_detector import multidomain_anomaly_detection
from model.alarm_process import multidomain_alarm_process


if __name__ == '__main__':
   
    multidomain_anomaly_detection()

    multidomain_alarm_process()
