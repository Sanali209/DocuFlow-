from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
import zipfile
import io
import json
import shutil
import uuid
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from .. import crud, models, schemas
from ..dependencies import get_db
from ..auth import verify_admin

router = APIRouter(tags=["documents"])

@router.post("/upload")
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

@router.post("/documents/", response_model=schemas.Document)
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    return crud.create_document(db=db, document=document)

@router.get("/documents/", response_model=List[schemas.Document])
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
    part_search: str | None = Query(None, description="Filter by part name/number in tasks"),
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
        assignee=assignee,
        part_search=part_search
    )
    return documents

@router.get("/documents/{document_id}", response_model=schemas.Document)
def read_document(document_id: int, db: Session = Depends(get_db)):
    db_document = crud.get_document(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@router.put("/documents/{document_id}", response_model=schemas.Document)
def update_document(document_id: int, document: schemas.DocumentUpdate, db: Session = Depends(get_db)):
    db_document = crud.update_document(db, document_id=document_id, document=document)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@router.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), role: str = Depends(verify_admin)):
    success = crud.delete_document(db, document_id=document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True}

@router.get("/journal/", response_model=List[schemas.JournalEntry])
def read_journal_entries(
    skip: int = 0,
    limit: int = 100,
    type: models.JournalEntryType | None = Query(None),
    status: models.JournalEntryStatus | None = Query(None),
    document_id: int | None = Query(None),
    db: Session = Depends(get_db)
):
    return crud.get_journal_entries(db, skip=skip, limit=limit, filter_type=type, filter_status=status, document_id=document_id)

@router.post("/journal/", response_model=schemas.JournalEntry)
def create_journal_entry(entry: schemas.JournalEntryCreate, db: Session = Depends(get_db)):
    return crud.create_journal_entry(db, entry)

@router.put("/journal/{entry_id}", response_model=schemas.JournalEntry)
def update_journal_entry(entry_id: int, entry: schemas.JournalEntryUpdate, db: Session = Depends(get_db)):
    db_entry = crud.update_journal_entry(db, entry_id, entry)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return db_entry

@router.delete("/journal/{entry_id}")
def delete_journal_entry(entry_id: int, db: Session = Depends(get_db)):
    success = crud.delete_journal_entry(db, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"ok": True}

@router.get("/tags", response_model=List[schemas.Tag])
def read_tags(db: Session = Depends(get_db)):
    return crud.get_tags(db)

def serialize_date(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj

@router.get("/backup")
def backup_data(db: Session = Depends(get_db)):
    try:
        backup_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "documents": [], "tasks": [], "materials": [], "tags": [],
            "journal_entries": [], "attachments": [], "settings": [],
            "filter_presets": [], "document_tags": []
        }

        documents = db.query(models.Document).all()
        for doc in documents:
            backup_data["documents"].append({
                "id": doc.id, "name": doc.name, "description": doc.description,
                "type": doc.type.value if doc.type else None,
                "status": doc.status.value if doc.status else None,
                "registration_date": serialize_date(doc.registration_date),
                "content": doc.content, "author": doc.author,
                "done_date": serialize_date(doc.done_date)
            })

        tasks = db.query(models.Task).all()
        for task in tasks:
            backup_data["tasks"].append({
                "id": task.id, "document_id": task.document_id,
                "material_id": task.material_id, "name": task.name,
                "status": task.status.value if task.status else None,
                "assignee": task.assignee
            })

        materials = db.query(models.Material).all()
        for material in materials:
            backup_data["materials"].append({"id": material.id, "name": material.name})

        tags = db.query(models.Tag).all()
        for tag in tags:
            backup_data["tags"].append({"id": tag.id, "name": tag.name})

        dt_records = db.execute(text("SELECT document_id, tag_id FROM document_tags")).fetchall()
        for dt in dt_records:
            backup_data["document_tags"].append({"document_id": dt[0], "tag_id": dt[1]})

        entries = db.query(models.JournalEntry).all()
        for entry in entries:
            backup_data["journal_entries"].append({
                "id": entry.id, "text": entry.text,
                "type": entry.type.value if entry.type else None,
                "status": entry.status.value if entry.status else None,
                "author": entry.author, "document_id": entry.document_id,
                "created_at": serialize_date(entry.created_at)
            })

        attachments = db.query(models.Attachment).all()
        for att in attachments:
            backup_data["attachments"].append({
                "id": att.id, "document_id": att.document_id,
                "journal_entry_id": att.journal_entry_id, "file_path": att.file_path,
                "filename": att.filename, "media_type": att.media_type,
                "created_at": serialize_date(att.created_at)
            })

        settings = db.query(models.Setting).all()
        for setting in settings:
            backup_data["settings"].append({"key": setting.key, "value": setting.value})

        presets = db.query(models.FilterPreset).all()
        for preset in presets:
            backup_data["filter_presets"].append({
                "id": preset.id, "name": preset.name, "config": preset.config
            })

        json_data = json.dumps(backup_data, indent=2, ensure_ascii=False)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('backup.json', json_data)
        zip_buffer.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"docuflow_backup_{timestamp}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.post("/restore")
async def restore_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        zip_buffer = io.BytesIO(content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            if 'backup.json' not in zip_file.namelist():
                raise HTTPException(status_code=400, detail="Invalid backup file: backup.json not found")
            json_data = zip_file.read('backup.json').decode('utf-8')
            backup_data = json.loads(json_data)

        required_keys = ["documents", "tasks", "materials", "tags", "journal_entries", "attachments", "settings", "filter_presets"]
        for key in required_keys:
            if key not in backup_data:
                raise HTTPException(status_code=400, detail=f"Invalid backup file: missing {key}")

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

        for material_data in backup_data.get("materials", []):
            material = models.Material(id=material_data["id"], name=material_data["name"])
            db.add(material)
        db.commit()

        for tag_data in backup_data.get("tags", []):
            tag = models.Tag(id=tag_data["id"], name=tag_data["name"])
            db.add(tag)
        db.commit()

        for doc_data in backup_data.get("documents", []):
            doc = models.Document(
                id=doc_data["id"], name=doc_data["name"], description=doc_data.get("description"),
                type=models.DocumentType(doc_data["type"]) if doc_data.get("type") else None,
                status=models.DocumentStatus(doc_data["status"]) if doc_data.get("status") else None,
                registration_date=date.fromisoformat(doc_data["registration_date"]) if doc_data.get("registration_date") else None,
                content=doc_data.get("content"), author=doc_data.get("author"),
                done_date=date.fromisoformat(doc_data["done_date"]) if doc_data.get("done_date") else None
            )
            db.add(doc)
        db.commit()

        for dt_data in backup_data.get("document_tags", []):
            db.execute(text("INSERT INTO document_tags (document_id, tag_id) VALUES (:doc_id, :tag_id)"),
                      {"doc_id": dt_data["document_id"], "tag_id": dt_data["tag_id"]})
        db.commit()

        for task_data in backup_data.get("tasks", []):
            task = models.Task(
                id=task_data["id"], document_id=task_data["document_id"],
                material_id=task_data.get("material_id"), name=task_data["name"],
                status=models.TaskStatus(task_data["status"]) if task_data.get("status") else None,
                assignee=task_data.get("assignee")
            )
            db.add(task)
        db.commit()

        for entry_data in backup_data.get("journal_entries", []):
            entry = models.JournalEntry(
                id=entry_data["id"], text=entry_data["text"],
                type=models.JournalEntryType(entry_data["type"]) if entry_data.get("type") else None,
                status=models.JournalEntryStatus(entry_data["status"]) if entry_data.get("status") else None,
                author=entry_data.get("author"), document_id=entry_data.get("document_id"),
                created_at=date.fromisoformat(entry_data["created_at"]) if entry_data.get("created_at") else None
            )
            db.add(entry)
        db.commit()

        for att_data in backup_data.get("attachments", []):
            att = models.Attachment(
                id=att_data["id"], document_id=att_data.get("document_id"),
                journal_entry_id=att_data.get("journal_entry_id"), file_path=att_data["file_path"],
                filename=att_data["filename"], media_type=att_data["media_type"],
                created_at=date.fromisoformat(att_data["created_at"]) if att_data.get("created_at") else None
            )
            db.add(att)
        db.commit()

        for setting_data in backup_data.get("settings", []):
            setting = models.Setting(key=setting_data["key"], value=setting_data["value"])
            db.add(setting)
        db.commit()

        for preset_data in backup_data.get("filter_presets", []):
            preset = models.FilterPreset(id=preset_data["id"], name=preset_data["name"], config=preset_data["config"])
            db.add(preset)
        db.commit()

        return {
            "success": True, "message": "Data restored successfully",
            "restored": {
                "documents": len(backup_data.get("documents", [])),
                "tasks": len(backup_data.get("tasks", []))
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
