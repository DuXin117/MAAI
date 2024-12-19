

PLC_PAR = ['EWS']
PLC_PAR = ['HIS', 'EWS']
PLC_CPT = [[0.9, 0.2, 0.5, 0.2],
           [0.1, 0.8, 0.5, 0.8]]

CPT_AS = [[0.95, 0.1], 
          [0.05, 0.9]]

parent_node_dict = {
    'DBS': {
        'parents': [],
        'cpd': [[0.14],
                [0.86]]
    },
    'HIS': {
        'parents': [],
        'cpd': [[0.32],
                [0.68]]
    },
    'EWS': {
        'parents': ['DBS', 'HIS'],
        'cpd': [[0.8, 0.28, 0.1, 0.05],
                [0.2, 0.72, 0.9, 0.95]]
    },
    'PLC1': {
        'parents': PLC_PAR,
        'cpd'    : PLC_CPT
    },
    'PLC2': {
        'parents': PLC_PAR,
        'cpd'    : PLC_CPT
    },
    'PLC3': {
        'parents': PLC_PAR,
        'cpd'    : PLC_CPT
    },

}

test_data    = ['EWS', 'PLC2', 'HIS', 'FV_10', 'LI_03']
cyber_device = ['DBS','HIS','EWS','PLC1','PLC2']

field_device_belonging = {
    "PLC1" : ["FV1", "FV2", "FV3", "TI1", "TI2", "TI3", "TI4", "FI3", "FI4", "FI5", "FI6", "PI1", "PI2", "LI2"], 
    "PLC2" : ["FV4", "FI1", "LI1", "FI2"]
}

for controller, device_list in field_device_belonging.items():
    for device in device_list:
        parent_node_dict[device] = {}
        parent_node_dict[device]['parents'] = [controller]
        parent_node_dict[device]['cpd'] = CPT_AS

cyb_devices = ['DBS', 'HIS', 'EWS', 'PLC1', 'PLC2', 'PLC3']
phy_devices = [
    "FV1", "FV2", "FV3", "FV4", "FI1", "LI1", "FI2", "TI1", "TI2", "TI3", "TI4", "FI3", "FI4", "FI5", "FI6", "PI1", "PI2", "LI2"
]
device_list = cyb_devices + phy_devices


cc_topology = [
    ('DBS', 'EWS'),
    ('HIS', 'EWS'),
    ('HIS', 'PLC1'),
    ('HIS', 'PLC2'),
    ('EWS', 'PLC1'),
    ('EWS', 'PLC2'),
    ('PLC1', 'FV1'),
    ('PLC1', 'FV2'),
    ('PLC1', 'FV3'),
    ('PLC1', 'TI1'),
    ('PLC1', 'TI2'),
    ('PLC1', 'TI3'),
    ('PLC1', 'TI4'),
    ('PLC1', 'FI3'),
    ('PLC1', 'FI4'),
    ('PLC1', 'FI5'),
    ('PLC1', 'FI6'),
    ('PLC1', 'PI1'),
    ('PLC1', 'PI2'),
    ('PLC1', 'LI2'),
    ('PLC2', 'FV4'),
    ('PLC2', 'FI1'),
    ('PLC2', 'LI1'),
    ('PLC2', 'FI2')
]

phy_topology = [
    ('FI5', 'FI6'),
    ('TI4', 'PI2'),
    ('TI4', 'FI6'),
    ('FI6', 'PI2'),
    ('PI2', 'FI6'),
    ('TI4', 'TI3'),
    ('TI3', 'FV3'),
    ('TI3', 'TI2'),
    ('FV3', 'FI4'),
    ('TI3', 'FI4'),
    ('TI2', 'FV2'),
    ('FV2', 'FI3'),
    ('TI1', 'FV1'),
    ('FV1', 'FI2'),
    ('TI1', 'PI1'),
    ('PI1', 'FI1'),
    ('LI1', 'FV4'),
    ('FI2', 'LI1'),
    ('FV4', 'FI2'),
    ('FI1', 'LI1'),
]

cp_topology = cc_topology + phy_topology
device_relationships = {}
for t in cp_topology:
    device_relationships.setdefault(t[0], []).append(t[1])
    device_relationships.setdefault(t[1], []).append(t[0])
