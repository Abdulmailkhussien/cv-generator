
import os
import subprocess
import re
import sys

def kill_server_on_port(port):
    print(f"Looking for process on port {port}...")
    try:
        # Run netstat to find the PID
        output = subprocess.check_output(f"netstat -aon | findstr :{port}", shell=True).decode()
        
        lines = output.strip().split('\n')
        pids = set()
        for line in lines:
            if "LISTENING" in line:
                parts = line.strip().split()
                # fast check: Proto, Local Address, Foreign Address, State, PID
                # TCP    0.0.0.0:1000           0.0.0.0:0              LISTENING       1234
                if parts[-1].isdigit():
                    pids.add(parts[-1])
        
        if not pids:
            print(f"No process found listening on port {port}.")
            return

        for pid in pids:
            print(f"Killing process with PID: {pid}")
            os.system(f"taskkill /F /PID {pid}")
            print("Process terminated.")
            
    except subprocess.CalledProcessError:
        print(f"No process found listening on port {port} (netstat returned exit code 1).")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    kill_server_on_port(1000)
    input("Press Enter to exit...")
