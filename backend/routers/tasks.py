from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..dependencies import get_db
from ..auth import verify_admin

router = APIRouter(tags=["tasks"])

@router.get("/documents/{document_id}/tasks", response_model=List[schemas.Task])
def read_tasks(document_id: int, db: Session = Depends(get_db)):
    return crud.get_tasks(db, document_id)

@router.post("/documents/{document_id}/tasks", response_model=schemas.Task)
def create_task(document_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, document_id, task)

@router.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = crud.update_task(db, task_id, task)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), role: str = Depends(verify_admin)):
    success = crud.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}

@router.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, db: Session = Depends(get_db), role: str = Depends(verify_admin)):
    success = crud.delete_attachment(db, attachment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"ok": True}

@router.get("/materials", response_model=List[schemas.Material])
def read_materials(db: Session = Depends(get_db)):
    return crud.get_materials(db)

@router.post("/materials", response_model=schemas.Material)
def create_material(material: schemas.MaterialCreate, db: Session = Depends(get_db)):
    return crud.create_material(db, material)

@router.put("/materials/{material_id}", response_model=schemas.Material)
def update_material(material_id: int, name: str, db: Session = Depends(get_db)):
    db_material = crud.update_material(db, material_id, name)
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")
    return db_material

@router.delete("/materials/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    success = crud.delete_material(db, material_id)
    if not success:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"ok": True}

@router.get("/parts", response_model=List[schemas.Part])
def read_parts(
    skip: int = 0,
    limit: int = 100,
    search: str | None = Query(None, description="Search by name or reg number"),
    material_id: int | None = Query(None, description="Filter by material ID"),
    min_width: float | None = Query(None, description="Min width"),
    max_width: float | None = Query(None, description="Max width"),
    min_height: float | None = Query(None, description="Min height"),
    max_height: float | None = Query(None, description="Max height"),
    db: Session = Depends(get_db)
):
    return crud.get_parts(
        db,
        skip=skip,
        limit=limit,
        search=search,
        material_id=material_id,
        min_width=min_width,
        max_width=max_width,
        min_height=min_height,
        max_height=max_height
    )

@router.post("/parts", response_model=schemas.Part)
def create_part(part: schemas.PartCreate, db: Session = Depends(get_db)):
    return crud.create_part(db, part)

@router.put("/parts/{part_id}", response_model=schemas.Part)
def update_part(part_id: int, part_data: dict = Body(...), db: Session = Depends(get_db)):
    db_part = crud.update_part(db, part_id, part_data)
    if not db_part:
        raise HTTPException(status_code=404, detail="Part not found")
    return db_part

@router.delete("/parts/{part_id}")
def delete_part(part_id: int, db: Session = Depends(get_db), role: str = Depends(verify_admin)):
    success = crud.delete_part(db, part_id)
    if not success:
        raise HTTPException(status_code=404, detail="Part not found")
    return {"ok": True}

@router.get("/stock", response_model=List[schemas.StockItem])
def read_stock(db: Session = Depends(get_db)):
    return crud.get_stock_items(db)

@router.post("/stock", response_model=schemas.StockItem)
def create_stock(item: schemas.StockItemCreate, db: Session = Depends(get_db)):
    return crud.create_stock_item(db, item)

@router.delete("/stock/{item_id}")
def delete_stock(item_id: int, db: Session = Depends(get_db), role: str = Depends(verify_admin)):
    success = crud.delete_stock_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}

@router.get("/workspaces", response_model=List[schemas.Workspace])
def read_workspaces(db: Session = Depends(get_db)):
    return crud.get_workspaces(db)

@router.post("/workspaces", response_model=schemas.Workspace)
def create_workspace(ws: schemas.WorkspaceCreate, db: Session = Depends(get_db)):
    return crud.create_workspace(db, ws)

@router.delete("/workspaces/{ws_id}")
def delete_workspace(ws_id: int, db: Session = Depends(get_db), role: str = Depends(verify_admin)):
    success = crud.delete_workspace(db, ws_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"ok": True}
