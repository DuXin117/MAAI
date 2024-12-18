'''
Author: Xin Du
Date: 2022-03-01 11:44:21
LastEditors: Xin Du
LastEditTime: 2024-12-18 17:51:59
Description: Experimental data recording class
'''

import copy
import os.path
import pandas as pd

from config.exp_config import record_cfg
from utils.utils import get_time_now

class ExpRecord():

    def __init__(self, exp_code = 'AD'):
        self.exp_code = exp_code
        file_dir = record_cfg['dir']
        file_name_prefix = record_cfg['file_name_prefix']
        self.data = copy.deepcopy(record_cfg['data'])

        file_name = f'{file_name_prefix}_{exp_code}.csv'
        self.file_path = os.path.join(file_dir, file_name)
        print('>>> Experimental data recording file path: ', self.file_path)
        self.record_id_inc_flag = False
        self.read_record_file()


    def add_ad_record(self, 
        seed = 0, best_ACC = 0, best_FAR = 0, mean_ACC = 0, mean_FAR = 0, best_PRE = 0, best_REC = 0, best_F1 = 0, detect_ratio = 0, model_para = '', run_time = 0, total_time = 0
    ):
        '''Record of abnormal detection results'''

        time_now = get_time_now('h:m:s')
        self.data = copy.deepcopy(record_cfg['data'])

 
        run_time = round(run_time, 1)
        total_time = round(total_time, 1)
        self.data['end_time']   = time_now
        self.data['seed']       = seed
        self.data['best_ACC']   = round(best_ACC, 3)
        self.data['best_FAR']   = round(best_FAR, 3)
        self.data['mean_ACC']   = round(mean_ACC, 3)
        self.data['mean_FAR']   = round(mean_FAR, 3)
        self.data['best_PRE']   = round(best_PRE, 3)
        self.data['best_REC']   = round(best_REC, 3)
        self.data['best_F1']    = round(best_F1 , 3)
        self.data['detect_ratio'] = detect_ratio
        self.data['model_para'] = model_para
        self.data['run_time']   = '{:2d}min{:.1f}s'.format(int(run_time/60), run_time%60)
        self.data['total_time'] = '{:2d}min{:.1f}s'.format(int(total_time/60), run_time%60)

        self.increase_record_id()
        self.add_record(self.data)

    def add_record(self, record_dict):
        record_dict_in = copy.deepcopy(record_dict)
        self.record = pd.read_csv(self.file_path)
        self.get_record_id()
        # The record line pointer has not changed
        if self.record_id_inc_flag == False:
            for dict_key in record_dict_in.keys():
                self.record[dict_key][self.record_id] = copy.deepcopy(record_dict_in[dict_key])
        else:
        # Create DF data and prepare for data insertion
            if self.record_id is None:
                self.record_id = 0
            record_df = pd.DataFrame(
                columns=self.get_record_names(), index=[self.record_id])
            for dict_key in record_dict_in.keys():
                record_df[dict_key][self.record_id] = copy.deepcopy(record_dict_in[dict_key])

            self.record = pd.concat([self.record, record_df], ignore_index=False, verify_integrity=False)
            self.record_id_inc_flag = False
        self.save()

    def read_record_file(self):
        if os.path.isfile(self.file_path):
            self.record = pd.read_csv(self.file_path)
            self.record_columns = self.record.columns
            print(">>> Read record files: ", self.file_path)

        else:
            print(">>> Record file not found!", self.file_path)
            self.record_columns = self.data.keys()
            self.record = pd.DataFrame(columns=self.record_columns)
            file_dir, file_name = os.path.split(self.file_path) 
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                
            self.record.to_csv(self.file_path, index=0)
            print("> Create record file:", self.file_path) 


    # ---- Obtain the index of the latest record in the file ----
    def get_record_id(self, inc_flog = False):

        if len(self.record.index) == 0:
            self.record_id = None
        # ID是否移动
        elif inc_flog == True: 
            self.record_id = self.record.index[-1] + 1
        elif inc_flog == False: 
            self.record_id = self.record.index[-1]
        return self.record_id

    def increase_record_id(self):
        self.record_id_inc_flag = True

    def save(self):
        self.record.to_csv(self.file_path, float_format='%.6f', index=0)

    def get_newest_record(self):
        record_id = self.get_record_id()
        newest_record = self.record[-1:]
        return newest_record, record_id

    def get_record_names(self):
        return self.record.columns

    def get_all_record(self):
        return self.record


