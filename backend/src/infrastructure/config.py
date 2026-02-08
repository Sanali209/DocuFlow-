import os
import json

CONFIG_FILE = os.path.join("static", "config.json")

def get_config_path():
    # Ensure static directory exists
    os.makedirs("static", exist_ok=True)
    return os.path.abspath(CONFIG_FILE)

def load_config():
    path = get_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(data):
    path = get_config_path()
    try:
        current = load_config()
        current.update(data)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(current, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_db_path():
    config = load_config()
    return config.get("database_path", "sql_app.db") # Default to local if not set

def get_db_url():
    db_path = get_db_path()
    
    # Ensure the directory for the database exists
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if db_dir and not os.path.exists(db_dir):
        print(f"Creating database directory: {db_dir}")
        os.makedirs(db_dir, exist_ok=True)
        
    return f"sqlite:///{db_path}"
