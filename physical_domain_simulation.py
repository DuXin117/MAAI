'''
Author: Xin Du
Date: 2024-11-20 09:22:16
LastEditors: Xin Du
LastEditTime: 2024-12-16 20:51:50
Description: FCC-Fractionator simulation
'''
import matlab.engine
import numpy as np
import pandas as pd
from utils.exp_plot import plot_multi_data_curve
from config.exp_config import exp_data_cfg


def main():

    sim_step = exp_data_cfg['FCC_sim']['sim_step']
    exp_data_file_path = exp_data_cfg['FCC_sim']['sim_file_path']
    
    print("Starting MATLAB engine ... ")
    eng = matlab.engine.start_matlab()
    print("Running simulation.m ... ")
    eng.simulation(matlab.double([sim_step]), nargout = 2)
    eng.quit()
    print("MATLAB engine stopped.")


if __name__ == "__main__":
    main()
