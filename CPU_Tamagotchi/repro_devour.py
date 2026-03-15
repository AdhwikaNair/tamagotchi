import sys
import os
import time
import subprocess
import psutil

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from pet_brain import PetBrain

def test_devour():
    brain = PetBrain()
    
    # 1. Start a dummy process (e.g., a notepad or a slow command)
    print("Starting dummy process...")
    proc = subprocess.Popen(['cmd.exe', '/c', 'timeout /t 30'], shell=True)
    pid = proc.pid
    print(f"Dummy process PID: {pid}")
    
    # Wait a bit
    time.sleep(1)
    
    # 2. Try to find it via get_top_offender
    print("Finding top offender...")
    offender = brain.get_top_offender()
    if offender:
        print(f"Top offender found: {offender['name']} (PID: {offender['pid']})")
    else:
        print("No top offender found.")
    
    # 3. Try to devour the dummy process specifically
    print(f"Attempting to devour PID {pid}...")
    success, message = brain.devour_process(pid)
    
    if success:
        print(f"Devour SUCCESSFUL! Message: {message}")
    else:
        print(f"Devour FAILED. Message: {message}")
        # Try to diagnose
        try:
            p = psutil.Process(pid)
            print(f"Process still exists: {p.status()}")
        except psutil.NoSuchProcess:
            print("Process no longer exists (maybe it finished already?).")
        except Exception as e:
            print(f"Error checking process: {e}")

if __name__ == "__main__":
    test_devour()
