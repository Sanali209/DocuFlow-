import subprocess
import sys
import time

# Start DocuFlow app in background
process = subprocess.Popen(
    [sys.executable, "-m", "docuflow.main"],
    stdout=open("app_stdout.log", "w"),
    stderr=open("app_stderr.log", "w"),
    cwd=r"D:\github\DocuFlow-"
)

print(f"Started app with PID {process.pid}")
time.sleep(8)

# Check if port is open
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("localhost", 8080))
sock.close()

if result == 0:
    print("App is running on port 8080")
else:
    print("App failed to start")
    with open("app_stderr.log") as f:
        print(f.read()[-500:])
