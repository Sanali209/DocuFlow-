from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, models, schemas
from ..dependencies import get_db
from ..gnc_parser import GNCParser
import os

router = APIRouter(tags=["parts"])

@router.get("/parts/{part_id}/gnc")
def get_part_gnc(part_id: int, db: Session = Depends(get_db)):
    part = db.query(models.Part).filter(models.Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
        
    if not part.gnc_file_path or not os.path.exists(part.gnc_file_path):
        raise HTTPException(status_code=404, detail="GNC file not found for this part")
        
    try:
        # We need to parse it and return the JSON structure expected by GncCanvas
        with open(part.gnc_file_path, 'r') as f:
            content = f.read()
            
        parser = GNCParser()
        sheet = parser.parse(content)
        return sheet # This returns the dict structure
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse GNC file: {str(e)}")
