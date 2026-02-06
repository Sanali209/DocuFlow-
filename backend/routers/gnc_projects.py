from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import SessionLocal
from .. import models, schemas, crud
import os

router = APIRouter(prefix="/api/gnc", tags=["gnc-projects"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get("/library-parts", response_model=List[schemas.Part])
async def get_library_parts(db: Session = Depends(get_db)):
    """
    Returns parts from the library that can be added to the nesting inventory.
    """
    return db.query(models.Part).limit(100).all()

@router.get("/orders/{order_id}/tasks", response_model=List[schemas.Task])
async def get_order_tasks(order_id: int, db: Session = Depends(get_db)):
    """
    Returns tasks for a specific order.
    """
    doc = db.query(models.Document).filter(models.Document.id == order_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    return doc.tasks

@router.get("/orders/{order_id}/project")
async def get_order_nesting_project(order_id: int, db: Session = Depends(get_db)):
    """
    Returns the full nesting project state (nesting_project.json) for an order.
    """
    doc = db.query(models.Document).filter(models.Document.id == order_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Standard path calculation
    base_path = "static/uploads/gncEditor"
    safe_name = "".join(c for c in doc.name if c.isalnum() or c in (' ', '-', '_')).strip()
    order_folder = f"{doc.id}_{safe_name}"
    project_file = os.path.join(base_path, order_folder, "nesting_project.json")
    
    if not os.path.exists(project_file):
        raise HTTPException(status_code=404, detail="Nesting project state not found for this order")
        
    import json
    with open(project_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@router.post("/save-order-nesting")
async def save_order_nesting(project: schemas.GNCProject, db: Session = Depends(get_db)):
    """
    Saves or updates the multi-sheet nesting result for an order.
    Uses OrderService to persist GNC files and nesting_project.json.
    """
    try:
        from ..services.orders import OrderService
        if project.order_id:
            # Update existing
            return OrderService.update_order_nesting(db, project.order_id, [s.model_dump() for s in project.sheets])
        else:
            # Create new (if name provided)
            return OrderService.save_multi_sheet_order(db, [s.model_dump() for s in project.sheets], project.name)
    except Exception as e:
        print(f"Error saving order nesting: {e}")
        raise HTTPException(status_code=500, detail=str(e))
