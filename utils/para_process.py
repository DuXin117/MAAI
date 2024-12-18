'''
Author: Xin Du
Date: 2022-03-24 14:15:22
LastEditors: Xin Du
LastEditTime: 2024-12-11 15:16:03
Description: 参数处理模块
'''


import copy
from config.model_config import model_para_grid, model_para_cfg




# ---- 获得实验模型的网格测试参数与配置参数 ----
# 在配置网格数据后将返回参数测试组
def get_exp_para(model_type):

    # -- 模型参数获取 --
    # 提取模型超参数网格
    para_grid = model_para_grid[model_type]
    # 提取模型参数字典
    model_para = model_para_cfg['model'][model_type]
    # -- 获得超参数网格测试组 --
    grid_para_names, para_grid_list = get_grid_para_list(para_grid)

    return model_para, grid_para_names, para_grid_list


# ---- 获得模型的网格参数列表 ----
def get_grid_para_list(test_para: dict):
    ''' 获取超参数网格训练参数组列表
    Args:
        test_para (dict): 待测试的参数组字典
    Returns:
        test_para_list(list): 待测参数名单
        test_para_group_list(list)：网格测试参数组
    '''
    test_para_list = list(test_para.keys())
    test_para_values = list(test_para.values())
    # 参数数目
    para_num = len(test_para_values)  
    # 参数索引指数
    ind_list = [i*0 for i in range(para_num)]
    max_ind_list = [len(para_set) for para_set in test_para_values]
    count = 0
    para_index_list = []
    while(ind_list[0] != max_ind_list[0]):
        #按照指数列表提取元素
        para_index_list.append(copy.deepcopy(ind_list))
        #print(ind_list)
        ind_list[-1] += 1
        #逆序遍历指数列表
        #索引到第二个元素即可
        #递进检查
        for l in range(para_num-1, 0, -1):
            if ind_list[l] == max_ind_list[l]:
                ind_list[l] = 0  # 清零
                ind_list[l-1] += 1  # 进一
        #更新指数
        count += 1
        if count > 3000:
            print(60 * '-')
            print('>>> 单组训练参数过多，仅保留前200个！')
            break

    test_para_group_list = []  # 迭代数据保存列表
    for ind_list in para_index_list:
        para_group_list = []
        for para_ind in range(para_num):
            para_group_list.append(test_para_values[para_ind][ind_list[para_ind]])
        test_para_group_list.append(para_group_list)

    return test_para_list, test_para_group_list


# ---- 通过网格参数设置获得实验编号 ----
# 考虑到TF保存模型的命名长度限制，控制长度
def get_exp_code(para_name_list=None, exp_para_group=None):
    exp_para_info = ''
    for para_ind, model_para_name in enumerate(para_name_list):
        model_exp_para = exp_para_group[para_ind]
        exp_para_info += model_para_name + \
             str(model_exp_para) + '_'

    return exp_para_info


def print_model_para(model_para):
    '''将模型参数打印到字符串中
    '''
    output_str = ''
    for key, value in model_para.items():
        output_str += f'{key}={value}\n'
    return output_str
