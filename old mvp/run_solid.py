import os
import shutil
import uvicorn
import webbrowser
import subprocess
import sys
from threading import Timer

def run_command(command, cwd=None, shell=True):
    print(f"Running: {command}")
    try:
        subprocess.check_call(command, cwd=cwd, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def build_frontend():
    print("\n--- Building Frontend ---")
    frontend_dir = os.path.join(os.getcwd(), "frontend")

    # Check if node_modules exists, if not install
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("Installing frontend dependencies...")
        run_command("npm install", cwd=frontend_dir)
    else:
        print("Frontend dependencies already installed (skipping npm install).")

    print("Running npm build...")
    # Standardize VITE_API_URL for the built frontend
    os.environ["VITE_API_URL"] = "/api"
    run_command("npm run build", cwd=frontend_dir)

def deploy_frontend():
    """
    Copies the built frontend from frontend/dist to static/
    """
    frontend_dist = os.path.join("frontend", "dist")
    static_dir = "static"
    static_assets = os.path.join(static_dir, "assets")

    if not os.path.exists(frontend_dist):
        print(f"Error: Frontend build not found in {frontend_dist}")
        print("Please run 'npm run build' in the frontend directory first.")
        return False

    print(f"Deploying frontend from {frontend_dist} to {static_dir}...")

    # Ensure static directory exists
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # Clear existing assets to avoid accumulation
    if os.path.exists(static_assets):
        print(f"Cleaning old assets: {static_assets}")
        shutil.rmtree(static_assets)

    # Copy new assets
    # We copy the contents of frontend/dist to static/
    # preventing overwrite of uploads if it exists in static/uploads
    for item in os.listdir(frontend_dist):
        s = os.path.join(frontend_dist, item)
        d = os.path.join(static_dir, item)
        
        if os.path.isdir(s):
            # For directories like 'assets', strict copy
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            # For files like 'index.html', copy/overwrite
            shutil.copy2(s, d)

    print("Frontend deployed successfully.")
    return True

def open_browser():
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    build_frontend()
    if deploy_frontend():
        print("Starting Solid Server (FastAPI + Svelte)...")
        print("Listening on http://localhost:8000")
        
        # Open browser after a short delay
        Timer(1.5, open_browser).start()
        
        # Add backend to sys.path so 'src' is importable as a top-level package
        sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
        
        # Run Uvicorn with the refactored Pro API
        uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
