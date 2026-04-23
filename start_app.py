import subprocess
import sys
import time

# Start DocuFlow app
process = subprocess.Popen(
    [sys.executable, "-m", "docuflow.main"],
    stdout=open("app_stdout.log", "w"),
    stderr=open("app_stderr.log", "w"),
    cwd=r"D:\github\DocuFlow-"
)

print(f"Started app with PID {process.pid}")
time.sleep(10)

# Check if port is open
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("localhost", 8082))
sock.close()

if result == 0:
    print("✅ App is running on port 8082")
else:
    print("❌ App failed to start")
    with open("app_stderr.log") as f:
        print(f.read()[-500:])
