import schedule
import time
import subprocess
import os

# runs a script on defined intervals.. needs the above packages

def run_script():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secureconnect.py")
    subprocess.run(["python3", script_path])

# Schedule the script to run every 5 minutes
schedule.every(1).minutes.do(run_script)

while True:
    schedule.run_pending()
    time.sleep(1)
