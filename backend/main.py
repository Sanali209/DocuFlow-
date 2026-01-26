import os
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
origins = [origin.strip() for origin in allowed_origins.split(",")] if allowed_origins else []
origins.extend([
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "*" # For sandbox
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/documents/", response_model=schemas.Document)
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    return crud.create_document(db=db, document=document)

@app.get("/documents/", response_model=List[schemas.Document])
def read_documents(
    skip: int = 0,
    limit: int = 100,
    search: str | None = Query(None, description="Search by document part name"),
    type: models.DocumentType | None = Query(None, description="Filter by document type"),
    status: models.DocumentStatus | None = Query(None, description="Filter by document status"),
    db: Session = Depends(get_db)
):
    documents = crud.get_documents(
        db,
        skip=skip,
        limit=limit,
        search_name=search,
        filter_type=type,
        filter_status=status
    )
    return documents

@app.get("/documents/{document_id}", response_model=schemas.Document)
def read_document(document_id: int, db: Session = Depends(get_db)):
    db_document = crud.get_document(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@app.put("/documents/{document_id}", response_model=schemas.Document)
def update_document(document_id: int, document: schemas.DocumentUpdate, db: Session = Depends(get_db)):
    db_document = crud.update_document(db, document_id=document_id, document=document)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    success = crud.delete_document(db, document_id=document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True}
