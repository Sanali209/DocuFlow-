from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import SessionLocal

router = APIRouter()

def check_db_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False

@router.get("/api/config-check")
def config_check():
    """
    Checks system configuration status.
    Returns JSON with status: 'configured', 'db_error', or 'unconfigured'.
    """
    if check_db_connection():
        return {"status": "configured", "message": "System is ready."}
    else:
        # In a real desktop app we might check if the file exists or path is set in config.ini
        # For now, if connection fails, we assume it's a DB error or path issue
        return {"status": "db_error", "message": "Cannot connect to database."}
