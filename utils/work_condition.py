import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from utils.exp_plot import plot_multi_data_curve


train_test_work_condition = []
# Random fluctuation setpoint: SP (1) - Oil and gas separator liquid level
train_test_work_condition.append([0,
    0.40, 0.29, 0.15, 0.10, 0.00, 
    0.03, 0.10, 0.21, 0.17, 0.12,
    0.16, 0.28, 0.44, 0.40, 0.33,
    0.31, 0.32, 0.45, 0.54, 0.68,
    0.76, 0.86, 0.95, 0.94, 0.98,   
    0.90, 0.86, 0.75, 0.74, 0.68, 
])

# Random fluctuation setpoint: SP (2) - top temperature of fractionation tower
train_test_work_condition.append([0,
    0.46, 0.42, 0.38, 0.18, 0.06,
    0.00, 0.11, 0.18, 0.05, 0.08,
    0.25, 0.38, 0.52, 0.43, 0.52,
    0.65, 0.52, 0.54, 0.69, 0.73,
    0.84, 0.72, 0.81, 0.89, 0.95,    
    0.98, 0.92, 0.81, 0.79, 0.75,  
])
# Random fluctuation setpoint: SP (3) - HN temperature
train_test_work_condition.append([0,
    0.32, 0.18, 0.02, 0.00, 0.09,
    0.18, 0.16, 0.03, 0.01, 0.22,
    0.38, 0.49, 0.48, 0.46, 0.25,
    0.32, 0.42, 0.68, 0.74, 0.65,
    0.73, 0.88, 0.99, 0.94, 0.90,  
    0.83, 0.78, 0.69, 0.64, 0.65,  
])
# Random fluctuation setpoint: SP (4) - LCO temperature
train_test_work_condition.append([0,
    0.93, 0.73, 0.99, 0.85, 0.61,
    0.63, 0.79, 0.75, 0.50, 0.53,
    0.57, 0.68, 0.49, 0.58, 0.32,
    0.31, 0.42, 0.39, 0.20, 0.10,
    0.01, 0.15, 0.19, 0.02, 0.16,    
    0.21, 0.25, 0.29, 0.32, 0.36,  
])
# Random fluctuation point: MV (1) - Temperature fluctuation of feed oil and gas
train_test_work_condition.append([0,
    0.45, 0.52, 0.38, 0.15, 0.03,
    0.00, 0.25, 0.18, 0.28, 0.12,
    0.07, 0.03, 0.10, 0.24, 0.31,
    0.41, 0.42, 0.63, 0.69, 0.75,
    0.81, 0.72, 0.83, 0.96, 0.93,    
    0.85, 0.72, 0.73, 0.66, 0.70,  
])
# Random fluctuation point: MV (2) - fluctuation of feed oil and gas flow rate
train_test_work_condition.append([0, 
    0.76, 0.58, 0.45, 0.39, 0.26,
    0.17, 0.15, 0.03, 0.10, 0.17,
    0.20, 0.23, 0.34, 0.48, 0.50,
    0.61, 0.66, 0.73, 0.68, 0.76,
    0.73, 0.78, 0.86, 0.83, 0.98,    
    0.93, 0.79, 0.66, 0.63, 0.68,  
])
# Random fluctuation point: MV (3) - Feed pressure fluctuation
train_test_work_condition.append([0, 
    0.46, 0.38, 0.35, 0.39, 0.36,
    0.27, 0.22, 0.14, 0.00, 0.07,
    0.18, 0.23, 0.34, 0.48, 0.50,
    0.61, 0.62, 0.73, 0.78, 0.76,
    0.81, 0.74, 0.89, 0.94, 0.88,  
    0.81, 0.64, 0.69, 0.64, 0.60,  
])


def gen_interp_curve(sim_time, select_point):
    """
    Extend the data of select_point to sim_time points through interpolation.
    """
    sel_num = len(select_point)
    
    if sel_num < 2:
        raise ValueError("At least two points are required for interpolation.")
    
    x_new = np.linspace(0, sel_num - 1, sim_time)
    x_orig = np.arange(sel_num)
    f = interp1d(x_orig, select_point, kind="quadratic", fill_value="extrapolate")
    y_smooth = f(x_new)
    
    return y_smooth


def control_work_condition(sim_time, sim_step, sim_mode = 'ORI_SIM', plot_fig = False):
    '''Generate simulated fluctuating operating conditions
        
        * Obtain a fluctuation experimental data set by customizing the fluctuation sequence, adding random fluctuations, and interpolating
        
        * By fixing the random noise seed and random sequence, it is easy to synchronize the instruction inputs of the original simulation and the reduced precision simulation
    '''

    sp_mv = []
    random_seed_list = [1, 2, 3, 4, 5, 6, 7]
    random_point_list = []
    step_per_min = int(60 / sim_step)

    scaler_boundary = [
        (68,     72),        # SP(1) 
        (244.33, 246.13),    # SP(2) 
        (527,    532),       # SP(3) 
        (753,    757),       # SP(4) 
        (790,    800),       # MV(1) 
        (3010,   3030),      # MV(2) 
        (1.71,   1.72),      # MV(3) 
    ]
    
    init_value = [70, 245.93, 530.33, 755.33, 793.70, 3025.85, 1.716863]

    random_point_list = train_test_work_condition
    
    noisy_scaler = 0.05
    extend_point = 3
    data_num = sim_time * step_per_min

    for i, random_point in enumerate(random_point_list):
        boundary = scaler_boundary[i]
        random_point[0] = (init_value[i] - boundary[0])/(boundary[1] - boundary[0])

        # ---- Expand by 2-3 times and then add a random number ----
        random_data = gen_interp_curve(extend_point * len(random_point), random_point)
        np.random.seed(random_seed_list[i])
        random_data += np.random.random(random_data.shape[0]) * noisy_scaler * 3

        random_data = gen_interp_curve(data_num, random_data)
        random_data = random_data * (boundary[1] - boundary[0]) + boundary[0]
        sp_mv.append(random_data)

    sp_mv = np.array(sp_mv)
    sp_mv =sp_mv.T
    sp_columns = ['SP1', 'SP2', 'SP3', 'SP4', 'MV1', 'MV2', 'MV3']

    if plot_fig:
        print(sp_mv.shape)
        data_num = sp_mv.shape[0]
        plot_multi_data_curve(
            t = np.arange(data_num),
            data = sp_mv,
            label = sp_columns,
            col_num = 3,
            fig_size = (9, 3),
        )

    sp_mv = sp_mv.tolist()
    return sp_mv
