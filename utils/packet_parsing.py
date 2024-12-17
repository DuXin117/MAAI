
from utils.utils import get_system_config, get_system_state
from scapy.all import *
from scapy.layers.inet import TCP, IP
from scapy.contrib.modbus import ModbusADURequest, ModbusADUResponse, ModbusPDU03ReadHoldingRegistersRequest, ModbusPDU03ReadHoldingRegistersResponse,ModbusPDU10WriteMultipleRegistersRequest, ModbusPDU10WriteMultipleRegistersResponse

config = get_system_config('parsing')

import copy

# ---- Modbus TCP packet parsing ----
def modbus_packet_parsing(packet=None):

    global config

    parsed_data = []
    parsed_field = {
        'sip' : None,
        'dip' : None,
    }

    sim_cfg = copy.deepcopy(config)
    tcp_field_list = sim_cfg['TCP']
    mbtcp_field_list = sim_cfg['MBTCP']
    derive_field_list = sim_cfg['DERIVE']

    if packet.haslayer(Raw):

        # ---- TCP field extraction ----
        tcp_layer = packet[TCP]
        for field_name in tcp_field_list:
            parsed_field[field_name] = tcp_layer.fields[field_name]

        # ----Virtual IP field supplement ----
        parsed_field['sip'], parsed_field['dip'] = generate_ip_port(sport=parsed_field['sport'], dport=parsed_field['dport'])

        # ---- MBTCP field extraction ----
        payload = bytes(packet[Raw].load)
        parse_payload = parse_modbus_payload(payload)

        # ---- Modbus field extraction ----
        mbtcp_field_list += ['funcCode']
        for i, field_name in enumerate(mbtcp_field_list):
            parsed_field[field_name] = parse_payload[i]
        parsed_field['modbus'] = parse_payload[len(mbtcp_field_list):]

        # Remove the response message
        if parsed_field['len'] == 6:
            return []

        # ---- Expand communication features and add extraction ----
        derived_features = add_derived_features(parsed_field['sport'], parsed_field['dport'])

        for i in range(len(derived_features)): 
            parsed_field[derive_field_list[i]] = derived_features[i]

        parsed_field['label'] = add_data_label(parsed_field['sport'], parsed_field['dport'])

        print('---- modbus tcp field-value ----')
        for key, value in parsed_field.items():
            print(f'> {key} : {value}')
        print()

        # parsed_data = list(parsed_field.keys())
        parsed_data = list(parsed_field.values())

    return parsed_data


def add_data_label(sport = None, dport = None):
    """Set data labels based on the simulation phase and devices with anomalies"""
    sim_state = get_system_state()
 
    if sim_state == 'NORMAL':
        label = 0

    elif sim_state == 'A_MITM':
        # Communication between abnormal ports
        port_list = [5021, 15021]
        if sport in port_list and dport in port_list:
            label = 1
        else:
            label = 0

    elif sim_state == 'A_FDI':
        port_list = [5021, 15011, 15031]
        if sport in port_list and dport in port_list:
            label = 2
        else:
            label = 0

    elif sim_state == 'A_DOS':
        port_list = [5021, 15031]
        if sport in port_list and dport in port_list:
            label = 3
        else:
            label = 0
    else:
        label = 0

    return label


# 参考文档：https://scapy.readthedocs.io/en/latest/api/scapy.contrib.modbus.html
# 补充方便遍历的端口号
device_config = get_system_config('modbus')
for device, info in device_config.items():
    server_port = info.get("server_port")
    client_port = info.get("client_port")
    device_config[device]['port_list'] = [server_port, client_port, client_port + 1]

def generate_ip_port(sport = None, dport = None):
    """Convert the source and destination ports of local simulation communication to obtain data with virtual communication IP"""

    global device_config

    src_ip = None
    dst_ip = None

    for device, info in device_config.items():
        if sport in info['port_list']:
            src_ip = info["virtual_ip"]
        if dport in info['port_list']:
            dst_ip = info["virtual_ip"]
        if src_ip and dst_ip:
            break
    return src_ip, dst_ip

# ---- Modbus load analysis ----
def parse_modbus_payload(payload):
    
    parsed_payload = []
    # Modbus TCP packet load analysis
    transaction_id, protocol_id, length, unit_id = struct.unpack(">HHHB", payload[:7])
    function_code = payload[7]

    # Modbus TCP fixed field characteristic values
    parsed_payload.append(transaction_id)
    parsed_payload.append(protocol_id)
    parsed_payload.append(length)
    parsed_payload.append(unit_id)
    parsed_payload.append(function_code)

    data = payload[8:]

    # ModbusPDU03ReadHoldingRegisters
    if function_code == 3:  
        # Request has 4 bytes of data (start_addr and quantity)
        if len(data) == 4:  

            start_addr, quantity = struct.unpack(">HH", data)
            parsed_payload.append(start_addr)
            parsed_payload.append(quantity)
            print(">>> Captured ModbusPDU03ReadHoldingRegistersRequest:")

        # Response has at least 2 bytes of data (byte_count and register_values)

        elif len(data) > 1:  
            byte_count = data[0]
            register_values = [struct.unpack(">H", data[i:i+2])[0] for i in range(1, byte_count, 2)]
            parsed_payload.append(byte_count)
            parsed_payload.append(register_values)
            
            print(">>> Captured ModbusPDU03ReadHoldingRegistersResponse:")

    # ModbusPDU16WriteMultipleRegisters
    elif function_code == 16:  
        if len(data) > 5:  # Request (start_addr, quantity, byte_count and register_values)
            start_addr, quantity, byte_count = struct.unpack(">HHB", data[:5])
            register_values = [struct.unpack(">H", data[i:i+2])[0] for i in range(5, 5 + byte_count, 2)]

            parsed_payload.append(start_addr)
            parsed_payload.append(quantity)
            parsed_payload.append(byte_count)
            parsed_payload.append(register_values)

            print(">>> Captured ModbusPDU16WriteMultipleRegistersRequest:")
            print()

        elif len(data) == 4:  # Response (start_addr and quantity)
            start_addr, quantity = struct.unpack(">HH", data)
            parsed_payload.append(start_addr)
            parsed_payload.append(quantity)
            print(">>> Captured ModbusPDU16WriteMultipleRegistersResponse:")
            print()
        
    return parsed_payload


# ---- Add sliding window communication features ----
class SlidingWindow:
    def __init__(self, time_unit):
        self.time_unit = time_unit
        self.window = deque()

    def add_packet(self, timestamp):
        self.window.append(timestamp)
        # Remove elements outside the window
        while self.window[-1] - self.window[0] > self.time_unit:
            self.window.popleft()

    def get_packets_per_time_unit(self):
        return len(self.window)

# Global variables for features
old_packet_timestamps = 0
total_packets = 0
# error_packets = 0
time_unit = 4  # Window size in seconds
sliding_window = SlidingWindow(time_unit)
# Create a dictionary to store traffic characteristics of different links
link_sliding_windows = {}


def add_derived_features(sport = None, dport = None):
    """Add additional features to abnormal analysis of communication traffic"""

    derived_features = []
    global link_sliding_windows
    # Update packet timestamps and calculate time difference
    # Get packet timestamp
    timestamp = time.time()

    # Update sliding window for the specific communication link (sport, dport)
    link_key = (sport, dport)
    link_key_inverse = (dport, sport)

    if link_key not in link_sliding_windows and link_key_inverse not in link_sliding_windows:
        link_sliding_windows[link_key] = {
            "window": SlidingWindow(time_unit=2),
            "old_packet_timestamp": 0
        }

    elif link_key_inverse in link_sliding_windows:
        link_key = link_key_inverse
    
    # Obtain the time difference of packet arrival
    time_diff = timestamp - link_sliding_windows[link_key]["old_packet_timestamp"]
    link_sliding_windows[link_key]["old_packet_timestamp"] = timestamp

    # Extract specific link sliding window
    sliding_window = link_sliding_windows[link_key]["window"]
    # Update sliding window
    sliding_window.add_packet(timestamp)

    # Obtain the number of data packets within the time window
    packets_per_xSec = sliding_window.get_packets_per_time_unit()

    derived_features.append(time_diff)
    derived_features.append(packets_per_xSec)

    return derived_features
