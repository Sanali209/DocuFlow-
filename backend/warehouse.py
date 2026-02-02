from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from . import crud, models, schemas
from .database import SessionLocal
from .auth import verify_admin

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Reservations ---
@router.get("/reservations", response_model=List[schemas.Reservation])
def read_reservations(task_id: int | None = Query(None), db: Session = Depends(get_db)):
    return crud.get_reservations(db, task_id)

@router.post("/reservations", response_model=schemas.Reservation)
def create_reservation(reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    return crud.create_reservation(db, reservation)

@router.delete("/reservations/{reservation_id}")
def delete_reservation(reservation_id: int, db: Session = Depends(get_db)):
    success = crud.delete_reservation(db, reservation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"ok": True}

# --- Consumptions ---
@router.get("/consumptions", response_model=List[schemas.Consumption])
def read_consumptions(task_id: int | None = Query(None), db: Session = Depends(get_db)):
    return crud.get_consumptions(db, task_id)

@router.post("/consumptions", response_model=schemas.Consumption)
def create_consumption(consumption: schemas.ConsumptionCreate, db: Session = Depends(get_db)):
    return crud.create_consumption(db, consumption)

@router.delete("/consumptions/{consumption_id}")
def delete_consumption(consumption_id: int, db: Session = Depends(get_db)):
    success = crud.delete_consumption(db, consumption_id)
    if not success:
        raise HTTPException(status_code=404, detail="Consumption not found")
    return {"ok": True}

# --- Audit Logs ---
@router.get("/audit-logs", response_model=List[schemas.AuditLog])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_audit_logs(db, skip=skip, limit=limit)
