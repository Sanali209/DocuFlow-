import os
import subprocess
import sys
import platform
import shutil

def run_command(command, cwd=None, shell=True):
    print(f"Running: {command}")
    try:
        subprocess.check_call(command, cwd=cwd, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main():
    print("Starting DocuFlow Build Process...")

    # 1. Build Frontend
    print("\n--- Building Frontend ---")
    frontend_dir = os.path.join(os.getcwd(), "frontend")

    # Check if node_modules exists, if not install
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("Installing frontend dependencies...")
        run_command("npm install", cwd=frontend_dir)
    else:
        print("Frontend dependencies already installed (skipping npm install).")

    print("Running npm build...")
    run_command("npm run build", cwd=frontend_dir)

    # 2. Package Backend with PyInstaller
    print("\n--- Packaging Backend ---")

    # Determine separator for --add-data
    # Windows uses ';', Linux/Mac uses ':'
    sep = ";" if platform.system() == "Windows" else ":"

    frontend_dist = os.path.join("frontend", "dist")
    static_dest = "static"

    add_data_arg = f"{frontend_dist}{sep}{static_dest}"

    pyinstaller_cmd = [
        "pyinstaller",
        "--name", "DocuFlow",
        "--onedir",
        "--clean",
        "--noconfirm",
        "--add-data", add_data_arg,
        os.path.join("backend", "main.py")
    ]

    # Convert list to string for shell execution (easier for simple commands)
    # or pass list to subprocess with shell=False
    cmd_str = " ".join(pyinstaller_cmd)
    run_command(cmd_str)

    print("\n--- Build Complete ---")
    print(f"Distributable is in: {os.path.join(os.getcwd(), 'dist', 'DocuFlow')}")

if __name__ == "__main__":
    main()
