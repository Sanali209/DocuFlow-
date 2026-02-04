import os
import json

CONFIG_FILE = "config.json"

def get_config_path():
    # In one-file/one-dir mode, we want it near the executable or script
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
    # Ensure it's an absolute path if it is something like "Z:/..."?
    # SQLAlchemy handles sqlite:///absolute/path/to/db
    # If it is a relative path, it treats it relative to CWD.
    
    # Check if user entered a full path
    return f"sqlite:///{db_path}"
