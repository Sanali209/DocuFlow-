from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, models, schemas
from ..dependencies import get_db

router = APIRouter(
    prefix="/assignees",
    tags=["assignees"]
)

@router.get("/", response_model=list[schemas.Assignee])
def read_assignees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assignees = crud.get_assignees(db, skip=skip, limit=limit)
    return assignees

@router.post("/", response_model=schemas.Assignee)
def create_assignee(assignee: schemas.AssigneeCreate, db: Session = Depends(get_db)):
    # Check if exists
    existing = db.query(models.Assignee).filter(models.Assignee.name == assignee.name).first()
    if existing:
        return existing
    return crud.create_assignee(db=db, assignee=assignee)

@router.put("/{assignee_id}", response_model=schemas.Assignee)
def update_assignee(assignee_id: int, assignee: schemas.AssigneeUpdate, db: Session = Depends(get_db)):
    db_assignee = crud.update_assignee(db, assignee_id=assignee_id, name=assignee.name)
    if db_assignee is None:
        raise HTTPException(status_code=404, detail="Assignee not found")
    return db_assignee

@router.delete("/{assignee_id}")
def delete_assignee(assignee_id: int, db: Session = Depends(get_db)):
    success = crud.delete_assignee(db, assignee_id=assignee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignee not found")
    return {"ok": True}
