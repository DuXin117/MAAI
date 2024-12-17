'''
Author: Xin Du
Date: 2024-11-20 09:08:18
LastEditors: Xin Du
LastEditTime: 2024-12-10 11:40:20
Description: file content
'''
import subprocess
import time


def start_program(name, script):
    """启动子程序并打开控制台"""
    return subprocess.Popen(["python", script], creationflags=subprocess.CREATE_NEW_CONSOLE)

def main():
    
    try:
        # 启动 simulation.py
        print("Starting physical_domain_simulation.py...")
        simulation_process = start_program("simulation", "physical_domain_simulation.py")
        
        # time.sleep(6)  # 等待 simulation.py 启动
        
        # 启动 work.py
        print("Starting cyber_domain_simulation.py...")
        work_process = start_program("work", "cyber_domain_simulation.py")

        # 等待子进程完成
        work_process.wait()
        simulation_process.wait()

        print("All programs have exited.")

    except KeyboardInterrupt:
        print("Terminating all programs...")
        work_process.terminate()
        simulation_process.terminate()


if __name__ == "__main__":
    
    main()
