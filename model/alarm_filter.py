
import copy

from config.bn_config import device_list, cyb_devices, phy_devices, device_relationships


def Spatiotemporal_alarm_filter(cp_alarms, filter_mode = 'window'):

    alpha = 0.4  # Smooth coefficient, controlling the weight ratio of historical data and new data
    threshold = 0.45  # Alarm determination threshold
    window_size=4
    window_weights = [0.1, 0.2, 0.3, 0.4]
    output_alarms = []
    # 时序滤波方法

        # ---- Filtering method 1: Window averaging filtering -----
    if 'window' in filter_mode:
        output_alarms = alarm_window_filter(cp_alarms, threshold, window_size, window_weights)
    cp_alarms = output_alarms

    # ---- Filtering method 2: Topological filtering -----
    if 'topology' in filter_mode:
        output_alarms = alarm_topology_filter(cp_alarms)

    # Split the alarm into information domain alarm and physical domain alarm
    filtered_cyb_alarms = []
    filtered_phy_alarms = []
    for t in range(len(output_alarms)):
        filtered_cyb_alarms.append([])
        filtered_phy_alarms.append([])
        for alarm in output_alarms[t]:
            if alarm in cyb_devices:
                filtered_cyb_alarms[t].append(alarm)
            elif alarm in phy_devices:
                filtered_phy_alarms[t].append(alarm)
    
    return filtered_cyb_alarms, filtered_phy_alarms


def alarm_window_filter(cp_alarms, threshold = 0.45,  window_size = 4, window_weights = [0.1, 0.2, 0.3, 0.4]):

    print('> ---- Use window weighted filtering ----')

    devices = device_list

    device_alert_history = {device: [0] * window_size for device in devices}  
    output_alarms = []
    for t, alarms in enumerate(cp_alarms):
        current_alerts = []
        for device in devices:
            if device in alarms:
                device_alert_history[device].append(1)  
            else:
                device_alert_history[device].append(0)  
            # Ensure that the sliding window size does not exceed the set value
            if len(device_alert_history[device]) > window_size:
                device_alert_history[device].pop(0) 
            # Calculate the weighted average alarm value within the sliding window
            average_alert_value = sum(w * v for w, v in zip(window_weights, device_alert_history[device]))

            if average_alert_value >= threshold:
                current_alerts.append(device)
        output_alarms.append(current_alerts)
    return output_alarms



def alarm_topology_filter(cp_alarms):

    print('> Use topology analysis weighted filtering ')
    output_alarms = []

    for cp_alarm in cp_alarms:
        if len(cp_alarm) < 2:
            output_alarm_list = cp_alarm
        else:
            output_alarm_list = []
            remain_alarm_list = copy.deepcopy(cp_alarm)
            for alarm in cp_alarm:
                if alarm in output_alarm_list:
                    continue
                remain_alarm_list.remove(alarm)
                related_device_list = query_related_devices(alarm)

                for remain_alarm in remain_alarm_list:
                    if remain_alarm in related_device_list:
                        if alarm not in output_alarm_list:
                            output_alarm_list.append(alarm)
                        if remain_alarm not in output_alarm_list:
                            output_alarm_list.append(remain_alarm)

                if alarm not in output_alarm_list:
                    remain_alarm_list.append(alarm)

        if len(cp_alarm) >= 2 and len(output_alarm_list) == 0:
            output_alarm_list.append(cp_alarm[0])
        output_alarms.append(output_alarm_list)

    return output_alarms


def query_related_devices(device_id):
    return device_relationships.get(device_id, [])
