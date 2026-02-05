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

@router.get("/stock-templates", response_model=List[schemas.GNCStockItem])
async def get_stock_templates():
    """
    Returns common sheet templates for nesting.
    These are 'session' stock items, not necessarily from the warehouse DB.
    """
    templates = [
        {"id": 1, "name": "Standard Sheet (3000x1500)", "width": 3000, "height": 1500, "material": "Steel", "quantity": 10},
        {"id": 2, "name": "Small Sheet (2000x1000)", "width": 2000, "height": 1000, "material": "Steel", "quantity": 5},
        {"id": 3, "name": "Square Sheet (1250x1250)", "width": 1250, "height": 1250, "material": "Aluminum", "quantity": 2},
    ]
    return templates

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

@router.post("/save-order-nesting")
async def save_order_nesting(project: schemas.GNCProject, db: Session = Depends(get_db)):
    """
    Saves the multi-sheet nesting result.
    In a real implementation, this would generate GNC files for each sheet and update the order tasks.
    For now, we'll simulate the save success and log the action.
    """
    # TODO: Implement GNC generation and file saving logic
    # project.sheets contains the GNC data for each sheet.
    
    return {"status": "success", "message": f"Saved project '{project.name}' with {len(project.sheets)} sheets."}
