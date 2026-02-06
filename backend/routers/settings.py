import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..dependencies import get_db
from ..auth import verify_admin

router = APIRouter(tags=["settings"])

DOC_NAME_REGEX = os.getenv("DOC_NAME_REGEX", r"(?si)Order:\s*(.*?)\s*Date:")

@router.post("/settings/test-path")
def test_path(path_data: schemas.PathCheck, role: str = Depends(verify_admin)):
    path = path_data.path
    if not os.path.exists(path):
         return {"ok": False, "error": "Path does not exist"}
    if not os.path.isdir(path):
         return {"ok": False, "error": "Path is not a directory"}
    if not os.access(path, os.R_OK):
         return {"ok": False, "error": "Path is not readable"} # Check read permission
    return {"ok": True}

@router.get("/settings/{key}", response_model=schemas.Setting)
def read_setting(key: str, db: Session = Depends(get_db)):
    setting = crud.get_setting(db, key)
    if not setting:
        if key == "doc_name_regex":
            return schemas.Setting(key="doc_name_regex", value=DOC_NAME_REGEX)
        return schemas.Setting(key=key, value="") # Default empty
    return setting

@router.put("/settings/{key}", response_model=schemas.Setting)
def update_setting(key: str, setting: schemas.Setting, db: Session = Depends(get_db), role: str = Depends(verify_admin)):
    return crud.set_setting(db, key, setting.value)

@router.put("/settings/", response_model=schemas.Setting)
def update_setting_body(
    setting: schemas.Setting,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin)
):
    return crud.set_setting(db, setting.key, setting.value)

@router.get("/filter-presets", response_model=List[schemas.FilterPreset])
def read_filter_presets(db: Session = Depends(get_db)):
    return crud.get_filter_presets(db)

@router.post("/filter-presets", response_model=schemas.FilterPreset)
def create_filter_preset(preset: schemas.FilterPresetCreate, db: Session = Depends(get_db)):
    return crud.create_filter_preset(db, preset)

@router.delete("/filter-presets/{preset_id}")
def delete_filter_preset(preset_id: int, db: Session = Depends(get_db)):
    success = crud.delete_filter_preset(db, preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"ok": True}

@router.get("/settings/database-config", response_model=schemas.DatabaseConfig)
def get_db_config(role: str = Depends(verify_admin)):
    from .. import config
    return schemas.DatabaseConfig(database_path=config.get_db_path())

@router.put("/settings/database-config")
def update_db_config(db_config: schemas.DatabaseConfig, role: str = Depends(verify_admin)):
    from .. import config
    import pathlib
    
    # Save to config file
    success = config.save_config({"database_path": db_config.database_path})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save database configuration")

    # Trigger reload by touching main.py
    # This works because uvicorn is started with --reload in run_solid.py
    main_py = pathlib.Path(__file__).parent.parent / "main.py"
    if main_py.exists():
        main_py.touch()
    
    return {"ok": True, "message": "Database path updated. System is refreshing..."}
