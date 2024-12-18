<!--
 * @Author: Xin Du
 * @Date: 2024-12-16 10:50:30
 * @LastEditors: Xin Du
 * @LastEditTime: 2024-12-18 11:55:01
 * @Description: file content
-->


# MAAI Project

## 1. Project Introduction


This project has open sourced an industrial cyber physical system simulation environment for experimental datasets and detection programs used in attack detection. More specifically, it includes: 

* The simulation system for petroleum catalytic cracking fractionation (FCC) unit includes cyber domain communication and control behavior simulation, as well as physical domain fractionation unit process simulation.
  
* Based on the above simulation system, various network attacks and system failure behaviors were simulated to generate a dataset for attack detection.
 
* A proposed attack fault identification method was validated based on a dataset.

The following introduces the use of simulation code, simulation data, and detection code.

## 2. ICPS simulation system

### 2.1 Components of the ICPS Simulation System
- **Information Domain**: Simulate the communication behaviors based on Modbus TCP among multiple devices and the control behaviors of PLCs through [pymodbus](https://pymodbus.readthedocs.io/en/latest/).
- **Physical Domain**: Based on the open-source FCC fractionation unit simulation [FCC-Fractionator](https://github.com/Baldea-Group/FCC-Fractionator) in Matlab, extract the fractionation tower and oil-gas separator parts as the physical process. 

![Testbed_Cyber_Domain](./doc/image/Testbed_Cyber_Domain.jpg)

![Testbed_Physical_Domain](./doc/image/Testbed_Physical_Domain.jpg)

- The following figure shows the simulation data interaction relationship among different devices in the information domain. Periodic data interaction is carried out among the devices to simulate the device polling communication in the ICPS system.

![ICPS_simulation](./doc/image/ICPS_simulation.jpg)

### 2.2 仿真系统使用


- Information Domain Simulation Python Environment
  - **npcap**: npcap-1.80
  - **Python Package Versions**:
```
python==1.6.13
pymodbus==2.4.0
scapy==2.5.0
```

- Physical Domain Simulation Environment
  - **Matlab**: Matlab R2018A
  - **matlabengine for Python**

- Simulation Run Preparation
  - Set the simulation run start time and duration dictionary `mode_config` for each mode in `./cyber_domain_simulation.py`.
  - Set the simulation run state through `sim_state`.

- Simulation Program Running
  - Execute the program `python simulation_console.py`. 


## 3. Attack fault simulation dataset


## 4. Attack fault identification

