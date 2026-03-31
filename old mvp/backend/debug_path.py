import sys
import os

# Adjust path to include root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.dependencies import SessionLocal
from src.application.services.settings_service import SettingsService

def check_path():
    service = SettingsService(SessionLocal)
    sidra_path = service.get_sidra_path()
    
    print(f"DEBUG: Sidra Path = '{sidra_path}'")
    
    if sidra_path:
        encoded = sidra_path.encode('utf-8')
        print(f"DEBUG: Encoded: {encoded}")
        
        exists = os.path.exists(sidra_path)
        print(f"DEBUG: os.path.exists = {exists}")
        
        if not exists:
            # Try stripping
            stripped = sidra_path.strip()
            print(f"DEBUG: Stripped exists = {os.path.exists(stripped)}")
            
            # Try cleaning quotes
            cleaned = sidra_path.strip('"').strip("'")
            print(f"DEBUG: Cleaned quotes exists = {os.path.exists(cleaned)}")

if __name__ == "__main__":
    check_path()
