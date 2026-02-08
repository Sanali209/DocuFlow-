import os
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel
from src.application.services.settings_service import SettingsService
from src.api.dependencies import get_settings_service

router = APIRouter(tags=["settings"])

class SettingUpdate(BaseModel):
    key: str
    value: str

class DatabaseConfig(BaseModel):
    database_path: str

@router.get("/settings/{key}")
def get_setting(key: str, service: SettingsService = Depends(get_settings_service)):
    value = service.get_setting(key)
    return {"key": key, "value": value}

@router.put("/settings/")
def update_setting(update: SettingUpdate, service: SettingsService = Depends(get_settings_service)):
    success = service.set_setting(update.key, update.value)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update setting")
    return {"status": "success"}

@router.get("/settings/database/config")
def get_database_config():
    # This reads from config.json via infrastructure config
    from src.infrastructure.config import load_config
    config = load_config()
    return {"database_path": config.get("database_path", "sql_app.db")}

@router.put("/settings/database/config")
def update_database_config(config: DatabaseConfig):
    # This triggers a full app reload in some systems
    # For now, we update the config file via infrastructure config
    from src.infrastructure.config import save_config
    try:
        save_config({"database_path": config.database_path})
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config-check")
def config_check(service: SettingsService = Depends(get_settings_service)):
    try:
        # Basic DB check
        db_ok = True
        try:
            from src.api.database import SessionLocal
            from sqlalchemy import text
            db = SessionLocal()
            db.execute(text("SELECT 1")).all()
            db.close()
        except Exception as e:
            print(f"DEBUG: Config Check DB failure: {e}")
            db_ok = False
            
        from src.infrastructure.config import load_config, get_db_path
        conf = load_config()
        
        # Path checks for sync
        mihtav_path = service.get_mihtav_path()
        sidra_path = service.get_sidra_path()
        
        paths = {
            "mihtav": {
                "configured": bool(mihtav_path),
                "path": mihtav_path,
                "accessible": os.path.exists(mihtav_path) if mihtav_path else False
            },
            "sidra": {
                "configured": bool(sidra_path),
                "path": sidra_path,
                "accessible": os.path.exists(sidra_path) if sidra_path else False
            }
        }
        
        needs_sync_config = not (paths["mihtav"]["configured"] and paths["sidra"]["configured"])
        
        return {
            "status": "configured" if db_ok and not needs_sync_config else "needs_config" if db_ok else "db_error",
            "message": "System is ready." if db_ok and not needs_sync_config else "Config needed",
            "needs_setup": not db_ok,
            "needs_sync_config": needs_sync_config,
            "current_db": get_db_path(),
            "paths": paths
        }
    except Exception as e:
        from src.infrastructure.config import get_db_path
        return {
            "status": "db_error",
            "message": f"Connection failed: {str(e)}",
            "needs_setup": True,
            "needs_sync_config": True,
            "current_db": get_db_path(),
            "paths": {}
        }

@router.post("/settings/test-path")
def test_path(path: str = Body(..., embed=True)):
    exists = os.path.exists(path)
    return {
        "path": path,
        "exists": exists,
        "is_directory": os.path.isdir(path) if exists else False,
        "accessible": exists
    }

@router.get("/settings/assignees/list")
def list_assignees(service: SettingsService = Depends(get_settings_service)):
    return service.list_assignees()

@router.post("/settings/assignees")
def create_assignee(name: str = Body(..., embed=True), service: SettingsService = Depends(get_settings_service)):
    success = service.create_assignee(name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to create assignee")
    return {"status": "success"}

@router.put("/settings/assignees/{assignee_id}")
def update_assignee(assignee_id: int, name: str = Body(..., embed=True), service: SettingsService = Depends(get_settings_service)):
    success = service.update_assignee(assignee_id, name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update assignee")
    return {"status": "success"}

@router.delete("/settings/assignees/{assignee_id}")
def delete_assignee(assignee_id: int, service: SettingsService = Depends(get_settings_service)):
    success = service.delete_assignee(assignee_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete assignee")
    return {"status": "success"}

# Filter Presets
class FilterPresetCreate(BaseModel):
    name: str
    config: str

@router.get("/filter-presets")
def list_presets(service: SettingsService = Depends(get_settings_service)):
    return service.list_filter_presets()

@router.post("/filter-presets")
def create_preset(preset: FilterPresetCreate, service: SettingsService = Depends(get_settings_service)):
    success = service.create_filter_preset(preset.name, preset.config)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to create filter preset")
    return {"status": "success"}

@router.delete("/filter-presets/{preset_id}")
def delete_preset(preset_id: int, service: SettingsService = Depends(get_settings_service)):
    success = service.delete_filter_preset(preset_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete filter preset")
    return {"status": "success"}
