import os
import httpx
import re
import shutil
import uuid
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from datetime import date

from . import crud, models, schemas
from .database import SessionLocal, engine
from sqlalchemy import text

# Create tables
models.Base.metadata.create_all(bind=engine)

# Migration for new columns in documents
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN author TEXT"))
        conn.commit()
    except Exception:
        pass

    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN description TEXT"))
        conn.commit()
    except Exception:
        pass

    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN done_date DATE"))
        conn.commit()
    except Exception:
        pass

    # Ensure content column exists (legacy migration)
    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN content TEXT"))
        conn.commit()
    except Exception:
        pass

# Ensure upload directory
os.makedirs("static/uploads", exist_ok=True)

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
        if key == "doc_name_regex":
            return schemas.Setting(key="doc_name_regex", value=DOC_NAME_REGEX)
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@app.put("/settings/", response_model=schemas.Setting)
def update_setting(setting: schemas.Setting, db: Session = Depends(get_db)):
    return crud.set_setting(db, setting.key, setting.value)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"static/uploads/{filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "file_path": f"/uploads/{filename}",
        "filename": file.filename,
        "media_type": file.content_type
    }

@app.post("/documents/scan")
async def scan_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()

    # Save file locally for attachment
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path_disk = f"static/uploads/{filename}"
    with open(file_path_disk, "wb") as f:
        f.write(content)

    file_path_url = f"/uploads/{filename}"

    # Get OCR URL from DB or use default
    db_setting = crud.get_setting(db, "ocr_url")
    ocr_url = db_setting.value if db_setting else OCR_SERVICE_URL
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
            print(f"OCR Service Error: {e}")
            raise HTTPException(status_code=502, detail="OCR Service Unavailable")

    # Get Regex from DB
    db_setting_regex = crud.get_setting(db, "doc_name_regex")
    regex_pattern = db_setting_regex.value if db_setting_regex else DOC_NAME_REGEX

    match = re.search(regex_pattern, markdown)
    extracted_name = match.group(1).strip() if match else ""

    return {
        "name": extracted_name,
        "content": markdown,
        "attachment": {
            "file_path": file_path_url,
            "filename": file.filename,
            "media_type": file.content_type
        }
    }

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
    tag: str | None = Query(None, description="Filter by tag name"),
    start_date: date | None = Query(None, description="Start date filter"),
    end_date: date | None = Query(None, description="End date filter"),
    date_field: str = Query("registration_date", description="Field to filter date on"),
    sort_by: str = "registration_date",
    sort_order: str = "desc",
    assignee: str | None = Query(None, description="Filter by task assignee"),
    db: Session = Depends(get_db)
):
    documents = crud.get_documents(
        db,
        skip=skip,
        limit=limit,
        search_name=search,
        filter_type=type,
        filter_status=status,
        filter_tag=tag,
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
        sort_by=sort_by,
        sort_order=sort_order,
        assignee=assignee
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

# --- Task Endpoints ---
@app.get("/documents/{document_id}/tasks", response_model=List[schemas.Task])
def read_tasks(document_id: int, db: Session = Depends(get_db)):
    return crud.get_tasks(db, document_id)

@app.post("/documents/{document_id}/tasks", response_model=schemas.Task)
def create_task(document_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, document_id, task)

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = crud.update_task(db, task_id, task)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    success = crud.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}

# --- Attachment Endpoints ---
@app.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, db: Session = Depends(get_db)):
    success = crud.delete_attachment(db, attachment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"ok": True}

# --- Tag Endpoints ---
@app.get("/tags", response_model=List[schemas.Tag])
def read_tags(db: Session = Depends(get_db)):
    return crud.get_tags(db)

# --- Filter Presets ---
@app.get("/filter-presets", response_model=List[schemas.FilterPreset])
def read_filter_presets(db: Session = Depends(get_db)):
    return crud.get_filter_presets(db)

@app.post("/filter-presets", response_model=schemas.FilterPreset)
def create_filter_preset(preset: schemas.FilterPresetCreate, db: Session = Depends(get_db)):
    return crud.create_filter_preset(db, preset)

@app.delete("/filter-presets/{preset_id}")
def delete_filter_preset(preset_id: int, db: Session = Depends(get_db)):
    success = crud.delete_filter_preset(db, preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"ok": True}

# Serve Static Files (Svelte)
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    app.mount("/uploads", StaticFiles(directory="static/uploads"), name="uploads")

    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join("static", full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # Otherwise serve index.html
        return FileResponse("static/index.html")
