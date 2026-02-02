import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import SessionLocal
from . import crud

router = APIRouter()

def check_db_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False

def check_sync_paths():
    """Check if sync folder paths are configured and accessible."""
    try:
        db = SessionLocal()
        mihtav_setting = crud.get_setting(db, "sync_mihtav_path")
        sidra_setting = crud.get_setting(db, "sync_sidra_path")
        
        db.close()
        
        paths_configured = {
            "mihtav": {
                "configured": bool(mihtav_setting and mihtav_setting.value),
                "path": mihtav_setting.value if mihtav_setting else None,
                "accessible": os.path.exists(mihtav_setting.value) if mihtav_setting and mihtav_setting.value else False
            },
            "sidra": {
                "configured": bool(sidra_setting and sidra_setting.value),
                "path": sidra_setting.value if sidra_setting else None,
                "accessible": os.path.exists(sidra_setting.value) if sidra_setting and sidra_setting.value else False
            }
        }
        return paths_configured
    except Exception as e:
        print(f"Error in check_sync_paths: {e}")
        return {"mihtav": {"configured": False}, "sidra": {"configured": False}}

@router.get("/api/config-check")
def config_check():
    """
    Checks system configuration status.
    Returns JSON with needs_config flag and detailed path status.
    """
    db_ok = check_db_connection()
    paths = check_sync_paths()
    
    # System needs config if either path is not configured
    needs_config = not (paths["mihtav"]["configured"] and paths["sidra"]["configured"])
    
    if not db_ok:
        return {
            "status": "db_error",
            "message": "Cannot connect to database.",
            "needs_config": True,
            "paths": paths
        }
    
    return {
        "status": "configured" if not needs_config else "needs_config",
        "message": "System is ready." if not needs_config else "Please configure sync folder paths.",
        "needs_config": needs_config,
        "paths": paths
    }

@router.post("/api/test-path")
def test_path(path: str):
    """Test if a given path is accessible."""
    exists = os.path.exists(path)
    is_dir = os.path.isdir(path) if exists else False
    return {
        "path": path,
        "exists": exists,
        "is_directory": is_dir,
        "accessible": exists and is_dir
    }
