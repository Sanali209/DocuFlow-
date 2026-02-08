import os
import sys
import uvicorn
import webbrowser
from threading import Timer

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def open_browser():
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # If running from source (dev mode), add backend to path
    if not getattr(sys, 'frozen', False):
        sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

    # Open browser after a short delay
    Timer(1.5, open_browser).start()
    
    print("Starting DocuFlow Pro...")
    print("Listening on http://localhost:8000")
    
    # Run Uvicorn pointing to the main app
    from src.api.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000)
