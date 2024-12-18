'''
Author: Xin Du
Date: 2023-01-29 15:40:12
LastEditors: Xin Du
LastEditTime: 2024-12-18 16:06:30
Description:  Experimental model parameter configuration
'''

from utils.utils import get_time_now

local_date = get_time_now('date')

# The threshold amplification factor of each model is adjusted based on the detection results of the model
al_threshold_ratio = {
    'DNN'    : [10 + 50 * i for i in range(1000)],
    'BILSTM' : [10 + 50 * i for i in range(1000)],
    'CNN'    : [10 + 50 * i for i in range(1000)],
    'MANN'   : [10 + 50 * i for i in range(1000)],
    'MANN'   : [10 + 50 * i for i in range(1000)],
    'TRAN'   : [10 + 50 * i for i in range(1000)],
}

ad_threshold_ratio = {
    'DNN'    : [0.3 + 0.02 * i for i in range(0, 400)],
    'BILSTM' : [0.3 + 0.02 * i for i in range(0, 400)],
    'CNN'    : [0.3 + 0.02 * i for i in range(0, 400)],
    'MANN'   : [0.3 + 0.02 * i for i in range(0, 400)],
    'TRAN'   : [0.3 + 0.02 * i for i in range(0, 400)],
}

model_para_grid = {
    'DNN' : {
        'lr'         : [0.0005, 0.001, 0.005],
        'epoch'      : [20, 50, 100],
        'batch_size' : [32, 64, 128],
        'dp'         : [0, 0.1, 0.2],
    },
    'BILSTM' : {
        'lr'          : [0.0005, 0.001, 0.005],
        'epoch'       : [20, 50, 100],
        'batch_size'  : [32, 64, 128],
        'dp'          : [0, 0.1, 0.2],
        'seq_len'     : [10],
    },
    'CNN' : {
        'lr'         : [0.0005, 0.001, 0.005],
        'epoch'      : [20, 50, 100],
        'batch_size' : [32, 64, 128],
        'dp'         : [0, 0.1, 0.2],
    },
    'MANN' : {
        'lr'         : [0.0005, 0.001, 0.005],
        'epoch'      : [20, 50, 100],
        'batch_size' : [32, 64, 128],
        'dp'         : [0, 0.1, 0.2],
    },
    'TRAN' : {
        'lr'         : [0.0005, 0.001, 0.005],
        'epoch'      : [20, 50, 100],
        'batch_size' : [32, 64, 128],
        'dp'         : [0, 0.1, 0.2]
    },
}

model_para_cfg = {
    'model': {
        'TRAN' : {
            'seq_len' : 10  ,
            'stride'  : 3  ,
        },
        'DNN': {
            'fc_nl'   : 2,
            'fc_nu'   : 296,
            'es_p'    : 10,
            'dp'      : 0.1,
        },
        'BILSTM' : {
            'fc_nl'   : 1      ,
            'fc_nu'   : 64     ,
            'dp'      : 0.1    ,
        }, 
        'CNN' : {
            'cnn_nu'    : 64     ,
            'cnn_nl'    : 2      ,
            'k_s'       : 3,
            'p_s'       : 2,
            'fc_nl'     : 1      ,
            'fc_nu'     : 128    ,
            'dp'        : 0.1    ,
        },
        'MANN' : {
            'enc_nu'    : 128    ,
            'mem_nu'    : 32     ,
            'mem_si'    : 128    ,
            'key_si'    : 128    , 
            'dp'        : 0.1
        },
    }
}
