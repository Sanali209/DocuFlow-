import os
import subprocess
import time

from loguru import logger


def kill_port_process(port: int) -> None:
    """
    Utility to identify and terminate any process occupying a specific TCP port.
    Specifically optimized for Windows development workflows.
    """
    try:
        # Use a faster check for Windows
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],  # noqa: S607
            capture_output=True,
            text=True,
            encoding="cp866",
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts: list[str] = line.split()
                if len(parts) >= 5:
                    pid: str = parts[-1]
                    if pid != str(os.getpid()) and pid != "0":
                        logger.info(f"Port {port} is busy. Killing PID {pid}...")
                        # Using taskkill /F to ensure the process is gone
                        subprocess.run(  # noqa: S603
                            ["taskkill", "/F", "/PID", pid],  # noqa: S607
                            capture_output=True,
                        )
                        # Give Windows a moment to release the socket
                        time.sleep(0.5)
    except Exception as e:
        logger.debug(f"Port killer error (ignoring): {e}")
