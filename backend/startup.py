import os
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import SessionLocal
from . import crud, config, models

router = APIRouter()

def check_db_connection():
    try:
        # This will try to connect to whatever is in config
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False

def check_sync_paths():
    """Check if sync folder paths are configured and accessible."""
    try:
        if not check_db_connection():
             return {"mihtav": {"configured": False}, "sidra": {"configured": False}}

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
    """
    db_ok = check_db_connection()
    
    # Check if we have a custom config saved
    conf = config.load_config()
    has_custom_conf = bool(conf.get("database_path"))
    
    if not db_ok:
        return {
            "status": "db_error",
            "message": "Cannot connect to database.",
            "needs_setup": True, # UI should redirect to setup
            "config": conf
        }
        
    paths = check_sync_paths()
    # System needs config if either path is not configured
    needs_sync_config = not (paths["mihtav"]["configured"] and paths["sidra"]["configured"])
    
    return {
        "status": "configured" if not needs_sync_config else "needs_config",
        "message": "System is ready." if not needs_sync_config else "Please configure sync folder paths.",
        "needs_setup": False,
        "needs_sync_config": needs_sync_config,
        "current_db": config.get_db_path(),
        "paths": paths
    }

@router.get("/api/config")
def get_config():
    return config.load_config()

@router.post("/api/config")
def update_config(data: dict = Body(...)):
    """Save new configuration (e.g. database_path)"""
    success = config.save_config(data)
    return {"ok": success}

@router.post("/api/test-path")
def test_path(path: str = Body(..., embed=True)):
    """Test if a given path is accessible."""
    exists = os.path.exists(path)
    is_dir = os.path.isdir(path) if exists else False
    
    # Check write permission if it's for DB? 
    # For now just existence
    
    return {
        "path": path,
        "exists": exists,
        "is_directory": is_dir,
        "accessible": exists
    }

def ensure_assignees_migrated(db: Session):
    """
    Ensures that all unique string assignees in tasks exist in the Assignee table.
    """
    try:
        # Get all distinct assignees from tasks that are not null/empty
        result = db.execute(text("SELECT DISTINCT assignee FROM tasks WHERE assignee IS NOT NULL AND assignee != ''"))
        task_assignees = [row[0] for row in result]
        
        # Get existing assignees in table
        existing_objs = db.query(models.Assignee).all()
        existing_names = set(a.name for a in existing_objs)
        
        for name in task_assignees:
            if name not in existing_names:
                print(f"Migrating assignee: {name}")
                new_asg = models.Assignee(name=name)
                db.add(new_asg)
                existing_names.add(name) # Prevent duplicates in same loop
        
        db.commit()
    except Exception as e:
        print(f"Error migrating assignees: {e}")

# Run migration on import/startup if DB is accessible
try:
    if check_db_connection():
        db = SessionLocal()
        ensure_assignees_migrated(db)
        db.close()
except Exception:
    pass
