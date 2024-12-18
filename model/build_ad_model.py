'''
Author: Xin Du
Date: 2023-12-11 11:28:25
LastEditors: Xin Du
LastEditTime: 2024-12-18 22:20:35
Description: DL-based reconstruction model
'''

import copy
import tensorflow as tf
import numpy as np
import os

from sklearn.metrics import accuracy_score, precision_score, f1_score, recall_score, confusion_matrix

from config.exp_config import exp_group_cfg, exp_data_cfg
from model.build_dl_model import build_dl_model
from sklearn.model_selection import train_test_split
from utils.file_operate import search_file_dir
from utils.utils import get_sub_seqs, get_time_now
from model.UATRAN import UAnomalyTransformer


def build_ad_model(exp_type, model_type, model_para, model_train_para, random_seed = 40):

    print('> model_train_para: ', model_train_para)
    epoch      = model_train_para['epoch']
    batch_size = model_train_para['batch_size']
    lr         = model_train_para['lr']
    seq_len    = model_train_para['seq_len']    
    
    if model_type in ['DNN', 'CNN', 'BILSTM', 'MANN']:
        
        model = ADModel(
                    exp_type = exp_type,
                    model_type = model_type,
                    model_para = model_para,
                    epochs = epoch,
                    batch_size = batch_size,
                    random_state = random_seed,
                    lr = lr,
                    seq_len = seq_len,
                )

    elif model_type == 'TRAN':
        model = UAnomalyTransformer(
                    exp_type = exp_type,
                    stride = model_para['stride'],
                    epochs = epoch,
                    batch_size = batch_size,
                    random_state = random_seed,
                    lr = lr,
                    seq_len=seq_len,
                )

    return model


def ad_metric(y_pred, y_true):
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    ACC = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average = 'binary')
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    FAR = fp / (fp + tn)  
    
    return ACC, FAR , precision, recall, f1


class ADModel():
    def __init__(self,
            exp_type     = 'cyber',
            model_type   = 'DNN',
            model_para   = None,
            epochs       = 30,
            batch_size   = 64,
            lr           = 0.001,
            seq_len      = 10,
            es_p         = 10,
            random_state = 40,
        ):
        self.model_type = model_type
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.seq_len = seq_len
        self.stride  = 1
        self.random_state = random_state
        self.model_para = copy.deepcopy(model_para)
        self.model_para['seq_len'] = self.seq_len
        self.exp_type = exp_type
        self.Anomaly_states_code = ''
        self.save_model_predict = False
        self.loss_weights = None

        if 'cyber' in self.exp_type:
            self.sp_input_dim = 7
            self.sp_output_dim = 7
            
        elif 'physical' in self.exp_type:
            self.sp_input_dim = 18
            self.sp_output_dim = 18
        else:
            raise ValueError('> ADModel: exp_type error!')

        self.model = build_dl_model(model_type, self.model_para, self.sp_input_dim, self.sp_output_dim)



    def fit(self, input_X, y):

        if self.model_type in ['BILSTM']: 

            train_X = get_sub_seqs(input_X, self.seq_len, self.stride)
            train_Y = input_X[self.seq_len-1 : , : ]
            spilt_train_X, spilt_val_X, spilt_train_Y, spilt_val_Y = train_test_split(train_X, train_Y, test_size = 0.20, random_state = self.random_state)
        
        elif self.model_type  in ['CNN']:
            train_X = input_X.reshape((input_X.shape[0], input_X.shape[1], 1))
            train_Y = train_X
            spilt_train_X, spilt_val_X, spilt_train_Y, spilt_val_Y = train_test_split(train_X, train_Y, test_size = 0.20, random_state = self.random_state)
        else:
            train_X = input_X
            train_Y = input_X

        spilt_train_X, spilt_val_X, spilt_train_Y, spilt_val_Y = train_test_split(train_X, train_Y, test_size = 0.20, random_state = self.random_state)

        print('\n')
        print('> Model input dimension:', spilt_train_X.shape[-1])
        print('> Model output dimension:', spilt_train_Y.shape[-1])
        print('\n')   
            
        loss = 'mse'
        metrics = [tf.keras.metrics.MeanSquaredError()]
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.lr),
            loss = loss, 
            loss_weights = self.loss_weights,
            metrics = metrics
        )

        train_history = self.model.fit(
            spilt_train_X, spilt_train_Y,
            epochs = self.epochs,
            batch_size = self.batch_size,
            # validation_split = 0.2,
            validation_data = (spilt_val_X, spilt_val_Y),
            shuffle = True,
            verbose = 0,
        )


    def eval(self, input_X):

        if self.model_type in ['BILSTM']:
            train_X = get_sub_seqs(input_X, self.seq_len, self.stride)
            input_X  = input_X[self.seq_len-1:, :]
            # label_Y = label[self.seq_len-1:, ]
            prediction  = self.model.predict(train_X)
        elif self.model_type  in ['CNN']:
            X = input_X.reshape((input_X.shape[0], input_X.shape[1], 1))
            prediction  = self.model.predict(X)
        else:
            prediction = self.model.predict(input_X)
        if 'physical' in self.exp_type:
            train_error = np.abs(prediction - input_X)
        # MSE
        elif 'cyber' in self.exp_type:
            train_error = np.mean(np.square(prediction - input_X), axis = 1)
            
        return train_error


    def decision_function(self, input_X, label):

        if self.model_type in ['BILSTM']:
            test_X = get_sub_seqs(input_X, self.seq_len, self.stride)
            test_Y  = input_X[self.seq_len-1:, :]
            pred_Y  = self.model.predict(test_X)
            test_X =input_X[self.seq_len-1:,]
            if 'physical' in self.exp_type:
                label_Y = label[self.seq_len-1:, ]
            else:
                label_Y = label[1:, ]
    
        elif self.model_type in ['CNN']:
            test_X = input_X
            test_X_reshape = input_X.reshape((input_X.shape[0], input_X.shape[1], 1))
            test_Y = input_X
            pred_Y  = self.model.predict(test_X_reshape)
            label_Y = label

        else:
            test_X = input_X
            label_Y = label
            pred_Y = self.model.predict(test_X)
        
        if 'physical' in self.exp_type:    
            y_score = np.abs(pred_Y - test_X)
        
        elif 'cyber' in self.exp_type:
            y_score = np.mean(np.square(pred_Y - test_X), axis = 1)


        if self.save_model_predict:

            prediction_dir = './exp_files/models/Prediction'
            model_code = f'{self.exp_type}_{self.model_type}'
            
            prediction_file_name = 'Precition_{0}_{1}.npy'.format(model_code, self.Anomaly_states_code)
            prediction_file_path = os.path.join(prediction_dir, prediction_file_name)
            test_data_file_path = os.path.join(prediction_dir, 'test_data.npy')
            
            np.save(prediction_file_path, pred_Y)
            print(f'>>> Save model prediction results : {prediction_file_path}')

        return y_score, label_Y
