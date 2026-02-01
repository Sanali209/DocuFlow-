import os
import httpx
import re
import shutil
import uuid
import json
import zipfile
import io
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from datetime import date, datetime

from . import crud, models, schemas
from .database import SessionLocal, engine
from sqlalchemy import text
from .gnc_parser import GNCParser, GNCSheet

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

    # Add material_id column to tasks
    try:
        conn.execute(text("ALTER TABLE tasks ADD COLUMN material_id INTEGER REFERENCES materials(id)"))
        conn.commit()
    except Exception:
        pass

    # Add gnc_file_path column to tasks
    try:
        conn.execute(text("ALTER TABLE tasks ADD COLUMN gnc_file_path TEXT"))
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

# --- Material Endpoints ---
@app.get("/materials", response_model=List[schemas.Material])
def read_materials(db: Session = Depends(get_db)):
    return crud.get_materials(db)

@app.post("/materials", response_model=schemas.Material)
def create_material(material: schemas.MaterialCreate, db: Session = Depends(get_db)):
    return crud.create_material(db, material)

@app.put("/materials/{material_id}", response_model=schemas.Material)
def update_material(material_id: int, name: str, db: Session = Depends(get_db)):
    db_material = crud.update_material(db, material_id, name)
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")
    return db_material

@app.delete("/materials/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    success = crud.delete_material(db, material_id)
    if not success:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"ok": True}

# --- GNC Endpoints ---
@app.post("/api/parse-gnc", response_model=GNCSheet)
async def parse_gnc(file: UploadFile = File(...)):
    """
    Parses an uploaded GNC file and returns its structured content.
    """
    try:
        content_bytes = await file.read()
        # Decode expecting text content, handle errors gracefully
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 or similar if needed, but UTF-8 is standard
            content = content_bytes.decode('latin-1')

        parser = GNCParser()
        sheet = parser.parse(content, filename=file.filename)
        return sheet
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse GNC file: {str(e)}")

# --- Backup and Restore Endpoints ---
def serialize_date(obj):
    """Helper to serialize date objects to ISO format"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj

@app.get("/backup")
def backup_data(db: Session = Depends(get_db)):
    """Export all database data as a zipped JSON file"""
    try:
        # Collect all data
        backup_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "documents": [],
            "tasks": [],
            "materials": [],
            "tags": [],
            "journal_entries": [],
            "attachments": [],
            "settings": [],
            "filter_presets": [],
            "document_tags": []
        }

        # Export documents
        documents = db.query(models.Document).all()
        for doc in documents:
            backup_data["documents"].append({
                "id": doc.id,
                "name": doc.name,
                "description": doc.description,
                "type": doc.type.value if doc.type else None,
                "status": doc.status.value if doc.status else None,
                "registration_date": serialize_date(doc.registration_date),
                "content": doc.content,
                "author": doc.author,
                "done_date": serialize_date(doc.done_date)
            })

        # Export tasks
        tasks = db.query(models.Task).all()
        for task in tasks:
            backup_data["tasks"].append({
                "id": task.id,
                "document_id": task.document_id,
                "material_id": task.material_id,
                "name": task.name,
                "status": task.status.value if task.status else None,
                "assignee": task.assignee,
                "gnc_file_path": task.gnc_file_path
            })

        # Export materials
        materials = db.query(models.Material).all()
        for material in materials:
            backup_data["materials"].append({
                "id": material.id,
                "name": material.name
            })

        # Export tags
        tags = db.query(models.Tag).all()
        for tag in tags:
            backup_data["tags"].append({
                "id": tag.id,
                "name": tag.name
            })

        # Export document_tags association
        from .models import document_tags
        dt_records = db.execute(text("SELECT document_id, tag_id FROM document_tags")).fetchall()
        for dt in dt_records:
            backup_data["document_tags"].append({
                "document_id": dt[0],
                "tag_id": dt[1]
            })

        # Export journal entries
        entries = db.query(models.JournalEntry).all()
        for entry in entries:
            backup_data["journal_entries"].append({
                "id": entry.id,
                "text": entry.text,
                "type": entry.type.value if entry.type else None,
                "status": entry.status.value if entry.status else None,
                "author": entry.author,
                "document_id": entry.document_id,
                "created_at": serialize_date(entry.created_at)
            })

        # Export attachments
        attachments = db.query(models.Attachment).all()
        for att in attachments:
            backup_data["attachments"].append({
                "id": att.id,
                "document_id": att.document_id,
                "journal_entry_id": att.journal_entry_id,
                "file_path": att.file_path,
                "filename": att.filename,
                "media_type": att.media_type,
                "created_at": serialize_date(att.created_at)
            })

        # Export settings
        settings = db.query(models.Setting).all()
        for setting in settings:
            backup_data["settings"].append({
                "key": setting.key,
                "value": setting.value
            })

        # Export filter presets
        presets = db.query(models.FilterPreset).all()
        for preset in presets:
            backup_data["filter_presets"].append({
                "id": preset.id,
                "name": preset.name,
                "config": preset.config
            })

        # Create JSON string
        json_data = json.dumps(backup_data, indent=2, ensure_ascii=False)

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('backup.json', json_data)

        zip_buffer.seek(0)

        # Return as downloadable file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"docuflow_backup_{timestamp}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@app.post("/restore")
async def restore_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Restore database from a zipped JSON backup file"""
    try:
        # Read the uploaded ZIP file
        content = await file.read()
        zip_buffer = io.BytesIO(content)
        
        # Extract JSON from ZIP
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            if 'backup.json' not in zip_file.namelist():
                raise HTTPException(status_code=400, detail="Invalid backup file: backup.json not found")
            
            json_data = zip_file.read('backup.json').decode('utf-8')
            backup_data = json.loads(json_data)

        # Validate backup data structure
        required_keys = ["documents", "tasks", "materials", "tags", "journal_entries", "attachments", "settings", "filter_presets"]
        for key in required_keys:
            if key not in backup_data:
                raise HTTPException(status_code=400, detail=f"Invalid backup file: missing {key}")

        # Clear existing data (in reverse order of dependencies)
        db.query(models.Attachment).delete()
        db.query(models.Task).delete()
        db.query(models.JournalEntry).delete()
        db.execute(text("DELETE FROM document_tags"))
        db.query(models.Document).delete()
        db.query(models.Material).delete()
        db.query(models.Tag).delete()
        db.query(models.FilterPreset).delete()
        db.query(models.Setting).delete()
        db.commit()

        # Restore materials first (needed by tasks)
        for material_data in backup_data.get("materials", []):
            material = models.Material(
                id=material_data["id"],
                name=material_data["name"]
            )
            db.add(material)
        db.commit()

        # Restore tags (needed by documents)
        for tag_data in backup_data.get("tags", []):
            tag = models.Tag(
                id=tag_data["id"],
                name=tag_data["name"]
            )
            db.add(tag)
        db.commit()

        # Restore documents
        for doc_data in backup_data.get("documents", []):
            doc = models.Document(
                id=doc_data["id"],
                name=doc_data["name"],
                description=doc_data.get("description"),
                type=models.DocumentType(doc_data["type"]) if doc_data.get("type") else None,
                status=models.DocumentStatus(doc_data["status"]) if doc_data.get("status") else None,
                registration_date=date.fromisoformat(doc_data["registration_date"]) if doc_data.get("registration_date") else None,
                content=doc_data.get("content"),
                author=doc_data.get("author"),
                done_date=date.fromisoformat(doc_data["done_date"]) if doc_data.get("done_date") else None
            )
            db.add(doc)
        db.commit()

        # Restore document_tags associations
        for dt_data in backup_data.get("document_tags", []):
            db.execute(text("INSERT INTO document_tags (document_id, tag_id) VALUES (:doc_id, :tag_id)"),
                      {"doc_id": dt_data["document_id"], "tag_id": dt_data["tag_id"]})
        db.commit()

        # Restore tasks
        for task_data in backup_data.get("tasks", []):
            task = models.Task(
                id=task_data["id"],
                document_id=task_data["document_id"],
                material_id=task_data.get("material_id"),
                name=task_data["name"],
                status=models.TaskStatus(task_data["status"]) if task_data.get("status") else None,
                assignee=task_data.get("assignee"),
                gnc_file_path=task_data.get("gnc_file_path")
            )
            db.add(task)
        db.commit()

        # Restore journal entries
        for entry_data in backup_data.get("journal_entries", []):
            entry = models.JournalEntry(
                id=entry_data["id"],
                text=entry_data["text"],
                type=models.JournalEntryType(entry_data["type"]) if entry_data.get("type") else None,
                status=models.JournalEntryStatus(entry_data["status"]) if entry_data.get("status") else None,
                author=entry_data.get("author"),
                document_id=entry_data.get("document_id"),
                created_at=date.fromisoformat(entry_data["created_at"]) if entry_data.get("created_at") else None
            )
            db.add(entry)
        db.commit()

        # Restore attachments
        for att_data in backup_data.get("attachments", []):
            att = models.Attachment(
                id=att_data["id"],
                document_id=att_data.get("document_id"),
                journal_entry_id=att_data.get("journal_entry_id"),
                file_path=att_data["file_path"],
                filename=att_data["filename"],
                media_type=att_data["media_type"],
                created_at=date.fromisoformat(att_data["created_at"]) if att_data.get("created_at") else None
            )
            db.add(att)
        db.commit()

        # Restore settings
        for setting_data in backup_data.get("settings", []):
            setting = models.Setting(
                key=setting_data["key"],
                value=setting_data["value"]
            )
            db.add(setting)
        db.commit()

        # Restore filter presets
        for preset_data in backup_data.get("filter_presets", []):
            preset = models.FilterPreset(
                id=preset_data["id"],
                name=preset_data["name"],
                config=preset_data["config"]
            )
            db.add(preset)
        db.commit()

        return {
            "success": True,
            "message": "Data restored successfully",
            "restored": {
                "documents": len(backup_data.get("documents", [])),
                "tasks": len(backup_data.get("tasks", [])),
                "materials": len(backup_data.get("materials", [])),
                "tags": len(backup_data.get("tags", [])),
                "journal_entries": len(backup_data.get("journal_entries", [])),
                "attachments": len(backup_data.get("attachments", [])),
                "settings": len(backup_data.get("settings", [])),
                "filter_presets": len(backup_data.get("filter_presets", []))
            }
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in backup file: {str(e)}")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


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
