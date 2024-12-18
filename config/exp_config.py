'''
Author: Xin Du
Date: 2023-06-25 22:57:20
LastEditors: Xin Du
LastEditTime: 2024-12-18 21:59:44
Description: Experimental parameter configuration
'''

from utils.utils import get_time_now

date_hour = get_time_now('date_time_all')
local_date = get_time_now('date')

exp_group_cfg = {

    'plot_pred_fig' : False,
    # Test random seed configuration
    'seed_list' : [40 + i for i in range(5)],

    # -------- Model training parameter --------
    'model_train_para' : {
        'epoch'     : 30,
        'batch_size': 64,
        # 'batch_size': 32,
        'lr'        : 0.0005,
        'seq_len'   : 10     ,
    },
    'model_pred_plot': False,
    'anomaly_plot': False,
}


exp_data_cfg = {
    # ---- FCC Physical Process Simulation Parameter Settings ----
    'FCC_sim' : {
        'sim_step' : 10,
        'sim_file_path' : f'./exp_files/FCC_Fractionator_{date_hour:s}.csv',
        # ------- 4 controller setpoint, 3  -------
        'set_point' : ['SP1', 'SP2', 'SP3', 'SP4', 'MV1', 'MV2', 'MV3'],
        # 18 sensor and actor point features, 4 control points, and 14 sensing points
        'feature_names' : ["FV1", "FV2", "FV3", "FV4", "FI1", "LI1", "FI2", "TI1", "TI2", "TI3", "TI4", "FI3", "FI4", "FI5", "FI6", "PI1", "PI2", "LI2"],
    },
    'cyber_sim' : {
        'feature_names' : ['sip', 'dip', 'sport', 'dport', 'seq', 'ack', 'window', 'transId', 'protoId', 'len', 'unitId', 'funcCode', 'modbus', 'delta_t', 'pac_arr'],
    }
}


# ----------------- Parameter configuration of experimental data recording module ------------------
record_cfg = {
    'dir': f'./exp_files/record/Exp-{local_date:s}',
    'file_name_prefix': 'Fractionator_AD',
    'data': {

        'end_time'    :  0,     
        'seed'        : 40,     
        # ---- Testing performance indicators ----
        'best_ACC'    :  0,     
        'best_FAR'    :  0,
        'best_PRE'    :  0,
        'best_REC'    :  0,
        'best_F1'     :  0,
        'mean_ACC'    :  0,
        'mean_FAR'    :  0,
        'detect_ratio':  0,    
        'model_para'  : '',     
        'run_time'    :  0,     
        'total_time'  :  0,
    },

}
