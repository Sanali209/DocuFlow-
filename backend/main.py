import os
import httpx
import re
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

from . import crud, models, schemas
from .database import SessionLocal, engine
from sqlalchemy import text

models.Base.metadata.create_all(bind=engine)

# Simple migration to ensure 'content' column exists
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN content TEXT"))
        conn.commit()
    except Exception:
        pass

    # Create settings table if not exists (handled by create_all, but just in case of weird state)
    # models.Base.metadata.create_all(bind=engine) covers it.

app = FastAPI()

DOC_NAME_REGEX = os.getenv("DOC_NAME_REGEX", r"(?si)Order:\s*(.*?)\s*Date:")
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://localhost:7860")

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

@app.get("/settings/{key}", response_model=schemas.Setting)
def read_setting(key: str, db: Session = Depends(get_db)):
    setting = crud.get_setting(db, key)
    if not setting:
        # Return default if not found
        if key == "ocr_url":
            return schemas.Setting(key="ocr_url", value=OCR_SERVICE_URL)
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@app.put("/settings/", response_model=schemas.Setting)
def update_setting(setting: schemas.Setting, db: Session = Depends(get_db)):
    return crud.set_setting(db, setting.key, setting.value)

@app.post("/documents/scan")
async def scan_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()

    # Get OCR URL from DB or use default
    db_setting = crud.get_setting(db, "ocr_url")
    ocr_url = db_setting.value if db_setting else OCR_SERVICE_URL
    # Remove trailing slash if user added it
    ocr_url = ocr_url.rstrip("/")

    async with httpx.AsyncClient() as client:
        try:
            files = {'file': (file.filename, content, file.content_type)}
            # Use timeout because OCR can be slow
            response = await client.post(f"{ocr_url}/process", files=files, timeout=60.0)
            response.raise_for_status()
            result = response.json()
            markdown = result.get("markdown", "")
        except Exception as e:
            # Fallback for demo if service not running (so UI doesn't break)
            # In production, we should log and raise.
            # Here I'll raise, but the UI should handle it.
            # If I want to allow testing without the service, I could mock here.
            # I'll just raise for now.
            print(f"OCR Service Error: {e}")
            raise HTTPException(status_code=502, detail="OCR Service Unavailable")

    match = re.search(DOC_NAME_REGEX, markdown)
    extracted_name = match.group(1).strip() if match else ""

    return {"name": extracted_name, "content": markdown}

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

@app.get("/journal/", response_model=List[schemas.JournalEntry])
def read_journal_entries(
    skip: int = 0,
    limit: int = 100,
    type: models.JournalEntryType | None = Query(None),
    status: models.JournalEntryStatus | None = Query(None),
    document_id: int | None = Query(None),
    db: Session = Depends(get_db)
):
    return crud.get_journal_entries(db, skip=skip, limit=limit, filter_type=type, filter_status=status, document_id=document_id)

@app.post("/journal/", response_model=schemas.JournalEntry)
def create_journal_entry(entry: schemas.JournalEntryCreate, db: Session = Depends(get_db)):
    return crud.create_journal_entry(db, entry)

@app.put("/journal/{entry_id}", response_model=schemas.JournalEntry)
def update_journal_entry(entry_id: int, entry: schemas.JournalEntryUpdate, db: Session = Depends(get_db)):
    db_entry = crud.update_journal_entry(db, entry_id, entry)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return db_entry

@app.delete("/journal/{entry_id}")
def delete_journal_entry(entry_id: int, db: Session = Depends(get_db)):
    success = crud.delete_journal_entry(db, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"ok": True}

# Serve Static Files (Svelte)
# This must be at the end to avoid conflicts with API routes
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API calls to pass through if they weren't caught above (though API routes are defined first)
        # But if it's a file in static root (like favicon.ico), serve it
        file_path = os.path.join("static", full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # Otherwise serve index.html
        return FileResponse("static/index.html")
