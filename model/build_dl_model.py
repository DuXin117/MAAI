'''
Author: Xin Du
Date: 2023-02-02 15:42:51
LastEditors: Xin Du
LastEditTime: 2024-12-18 17:37:32
Description: file content
'''
import numpy as np
import tensorflow as tf

from config.exp_config import exp_group_cfg
from tensorflow import keras
from model.MANN_model import MemoryAugmentedNN


def build_dl_model(model_type, model_para, input_dim, output_dim):

    if model_type == 'DNN':
        model = DNN_model(
            input_dim = input_dim,
            output_dim = output_dim,
            fc_nu = 296,
            fc_nl = 2,
            dropout = model_para['dp'],
            act = 'elu'
        )
        print('>>> Building a DNN model ')

    elif model_type == 'CNN':
        model = Conv1D_model(
            input_dim = input_dim,
            output_dim = output_dim,
            cnn_nu = 128, 
            cnn_nl = 2, 
            # network anomaly detector
            k_s = 2,
            p_s = 1,  
            # physical anomaly detector
            # k_s = 3,
            # p_s = 2,            
            fc_nu = 128,
            fc_nl = 1,
            dp = model_para['dp'],
            act = 'elu'
        )
        print('>>> Building a CNN-1D model')

    elif model_type == 'BILSTM':
        print('>>> Building a BILSTM model')
        model = BILSTM_model(
            input_dim = input_dim,
            output_dim = output_dim,
            fc_nu = model_para['fc_nu'],
            fc_nl = model_para['fc_nl'],
            dp = model_para['dp'],
            seq_len = model_para['seq_len'],
            act = 'elu'
        )

    elif model_type in ['MANN']:
        print('>>> Building a Memory Augmented NN model ')
        model = MemoryAugmentedNN(
            input_dim   = input_dim,
            output_dim  = output_dim,
            enc_dim     = model_para['enc_nu'],
            memory_units= model_para['mem_nu'],
            memory_size = model_para['mem_si'],
            key_size    = model_para['key_si'],
            dropout     = model_para['dp'],
            activation  = 'elu',
        )

    return model


def DNN_model(
        input_dim = 18, 
        output_dim = 18, 
        fc_nu = 296, 
        fc_nl = 2, 
        act ='elu', 
        dropout = 0.1):
    
    model_layers = [fc_nu for _ in range(fc_nl)]
    inputs = keras.layers.Input(
            shape=(input_dim, ), name='Input')
    for i in range(0, fc_nl):
        if i == 0:
            x = inputs
        x = keras.layers.Dense(
                model_layers[i],
                activation=act,
                kernel_initializer='glorot_uniform',
                name= f'fc_layer_{i:d}')(x)
        x = keras.layers.Dropout(dropout)(x)

    outputs = keras.layers.Dense(
                output_dim,
                kernel_initializer='glorot_uniform',
                name='output_layer')(x)

    return keras.Model(inputs, outputs)


def BILSTM_model(
    input_dim = 18, 
    output_dim = 18,
    fc_nu = 64, 
    fc_nl = 1, 
    seq_len = 10,
    act ='elu', 
    dp = 0.1
):
    
    model_layers = [fc_nu for _ in range(fc_nl)]
    inputs = keras.Input(shape=(seq_len, input_dim))
    for i in range(fc_nl):
        if i == 0:
            x = inputs
        x = keras.layers.Bidirectional(keras.layers.LSTM(
                model_layers[i],
                activation=act,
                kernel_initializer='glorot_uniform', 
                return_sequences=True,
                name=f'bilstm_layer_{i:d}'))(x)
        x = keras.layers.Dropout(dp)(x)

    x = keras.layers.Bidirectional(
            keras.layers.LSTM(
                output_dim,         
                return_sequences=False, 
                name = 'output_layer_0'
            )
        )(x)
    outputs = keras.layers.Dense(output_dim)(x)

    return keras.Model(inputs, outputs)



def Conv1D_model(
        input_dim = 18, 
        output_dim = 18,
        cnn_nu = 64, 
        cnn_nl = 2, 
        k_s = 3,
        p_s = 2,
        fc_nu = 128,
        fc_nl = 1,
        act ='elu', 
        dp = 0.1
    ):

    inputs = keras.layers.Input(shape=(input_dim, 1), name='Input')
    cnn1d_layers = [cnn_nu for _ in range(cnn_nl)]
    fc_layers = [fc_nu for _ in range(fc_nl)]
    x = keras.layers.Conv1D(filters=64, kernel_size=k_s, activation=act)(inputs)
    x = keras.layers.MaxPooling1D(pool_size=p_s)(x)
    x = keras.layers.Conv1D(filters=64, kernel_size=k_s, activation=act)(x)
    x = keras.layers.MaxPooling1D(pool_size=p_s)(x)
    x = keras.layers.Flatten()(x)
    for i in range(0, fc_nl):
        if i == 0:
            x = keras.layers.Dense(
                    fc_nu,
                    activation=act,
                    kernel_initializer='glorot_uniform',
                    name= f'fc_layer_{i:d}')(x)
        else:
            x = keras.layers.Dense(
                    fc_nu,
                    activation=act,
                    kernel_initializer='glorot_uniform',
                    name= f'fc_layer_{i:d}')(x)
        x = keras.layers.Dropout(dp)(x)
    
    outputs = keras.layers.Dense(
                output_dim,
                activation = act,
                kernel_initializer='glorot_uniform',
                name='output_layer')(x)

    return keras.Model(inputs, outputs)
