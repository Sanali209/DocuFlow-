import os
import sys

# Ensure backend is in path
backend_path = os.path.join(os.getcwd(), 'backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

try:
    from src.api.database import SessionLocal
    from src.application.services.settings_service import SettingsService
except ImportError as e:
    print(f"Import Error: {e}")
    # Try appending just 'src' if needed, but usually backend root is enough
    sys.exit(1)

def check():
    try:
        s = SettingsService(SessionLocal)
        path = s.get_sidra_path()
        print(f"Service sees: '{path}'")
        print(f"Repr: {repr(path)}")
        
        if path:
             exists = os.path.exists(path)
             print(f"Exists: {exists}")
             if not exists:
                 print(f"  Trying stripped: {os.path.exists(path.strip())}")
        else:
            print("Path is empty or None")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check()
