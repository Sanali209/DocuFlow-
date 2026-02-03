from sqlalchemy.orm import Session, subqueryload
from sqlalchemy import desc, asc, or_, and_
from . import models, schemas
from datetime import date
import os

def get_documents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search_name: str | None = None,
    filter_type: models.DocumentType | None = None,
    filter_status: models.DocumentStatus | None = None,
    filter_tag: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    date_field: str = "registration_date",
    sort_by: str = "registration_date",
    sort_order: str = "desc",
    assignee: str | None = None,
    part_search: str | None = None # New parameter
):
    query = db.query(models.Document).options(
        subqueryload(models.Document.tasks).subqueryload(models.Task.material),
        subqueryload(models.Document.journal_entries).subqueryload(models.JournalEntry.attachments),
        subqueryload(models.Document.attachments),
        subqueryload(models.Document.tags)
    )

    if search_name:
        search_pattern = f"%{search_name}%"
        query = query.filter(or_(
            models.Document.name.like(search_pattern),
            models.Document.description.like(search_pattern),
            models.Document.content.like(search_pattern)
        ))
        
    if part_search:
        # Filter documents that have tasks containing the matching part
        part_pattern = f"%{part_search}%"
        query = query.join(models.Document.tasks).join(models.Task.parts).filter(or_(
             models.Part.name.like(part_pattern),
             models.Part.registration_number.like(part_pattern)
        ))

    if filter_type:
        query = query.filter(models.Document.type == filter_type)

    if filter_status:
        query = query.filter(models.Document.status == filter_status)

    if filter_tag:
        query = query.join(models.Document.tags).filter(models.Tag.name == filter_tag)

    if assignee:
        query = query.join(models.Document.tasks).filter(models.Task.assignee == assignee)

    # Date Range Filtering
    if start_date or end_date:
        if hasattr(models.Document, date_field):
            column = getattr(models.Document, date_field)
            if start_date:
                query = query.filter(column >= start_date)
            if end_date:
                query = query.filter(column <= end_date)

    if hasattr(models.Document, sort_by):
        column = getattr(models.Document, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
    else:
        query = query.order_by(desc(models.Document.registration_date))

    return query.offset(skip).limit(limit).all()

def get_tags(db: Session):
    return db.query(models.Tag).all()

def _sync_tags(db: Session, db_document: models.Document, tags: list[str] | None):
    if tags is None:
        return

    # Clear existing tags if you want to replace, or merge?
    # Usually "update" with a list means replace the list.
    db_document.tags = []

    for tag_name in tags:
        tag_name = tag_name.strip()
        if not tag_name:
            continue

        db_tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
        if not db_tag:
            db_tag = models.Tag(name=tag_name)
            db.add(db_tag)
            # Flush to get ID if needed, but adding to session is enough for relationship

        if db_tag not in db_document.tags:
            db_document.tags.append(db_tag)

def create_document(db: Session, document: schemas.DocumentCreate):
    # Set default date if not provided
    reg_date = document.registration_date if document.registration_date else date.today()

    db_document = models.Document(
        name=document.name,
        description=document.description,
        type=document.type,
        status=document.status,
        registration_date=reg_date,
        content=document.content,
        author=document.author,
        done_date=document.done_date
    )

    _sync_tags(db, db_document, document.tags)

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    if document.attachments:
        for att in document.attachments:
            db_att = models.Attachment(
                document_id=db_document.id,
                file_path=att.file_path,
                filename=att.filename,
                media_type=att.media_type,
                created_at=date.today()
            )
            db.add(db_att)
        db.commit()
        db.refresh(db_document)

    return db_document

def get_document(db: Session, document_id: int):
    return db.query(models.Document).filter(models.Document.id == document_id).first()

def update_document(db: Session, document_id: int, document: schemas.DocumentUpdate):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not db_document:
        return None

    update_data = document.model_dump(exclude_unset=True)
    attachments_data = update_data.pop("attachments", None)
    tags_data = update_data.pop("tags", None)

    for key, value in update_data.items():
        setattr(db_document, key, value)

    if tags_data is not None:
        _sync_tags(db, db_document, tags_data)

    # Note: attachments_data is a dict after model_dump(), while document.attachments are Pydantic objects
    # In create_document, we access Pydantic object attributes (att.file_path)
    # In update_document, we access dict keys (att['file_path'])
    if attachments_data:
        for att in attachments_data:
            db_att = models.Attachment(
                document_id=db_document.id,
                file_path=att['file_path'],
                filename=att['filename'],
                media_type=att['media_type'],
                created_at=date.today()
            )
            db.add(db_att)

    db.commit()
    db.refresh(db_document)
    return db_document

def delete_document(db: Session, document_id: int):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_document:
        # Delete attachments files
        for att in db_document.attachments:
             try:
                # att.file_path is like "/uploads/filename"
                # actual path is "static/uploads/filename"
                if att.file_path.startswith("/uploads/"):
                     # Securely get filename
                     filename = os.path.basename(att.file_path)
                     file_path = os.path.join("static/uploads", filename)
                     if os.path.exists(file_path):
                        os.remove(file_path)
             except Exception as e:
                 print(f"Error deleting file {att.file_path}: {e}")

        db.delete(db_document)
        db.commit()
        return True
    return False

def get_setting(db: Session, key: str):
    return db.query(models.Setting).filter(models.Setting.key == key).first()

def set_setting(db: Session, key: str, value: str):
    db_setting = get_setting(db, key)
    if db_setting:
        db_setting.value = value
    else:
        db_setting = models.Setting(key=key, value=value)
        db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def get_journal_entries(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filter_type: models.JournalEntryType | None = None,
    filter_status: models.JournalEntryStatus | None = None,
    document_id: int | None = None
):
    query = db.query(models.JournalEntry).options(subqueryload(models.JournalEntry.attachments))
    if filter_type:
        query = query.filter(models.JournalEntry.type == filter_type)
    if filter_status:
        query = query.filter(models.JournalEntry.status == filter_status)
    if document_id:
        query = query.filter(models.JournalEntry.document_id == document_id)
        
    return query.order_by(models.JournalEntry.created_at.desc()).offset(skip).limit(limit).all()

def create_journal_entry(db: Session, entry: schemas.JournalEntryCreate):
    entry_date = entry.created_at if entry.created_at else date.today()
    db_entry = models.JournalEntry(
        text=entry.text,
        type=entry.type,
        status=entry.status,
        author=entry.author,
        document_id=entry.document_id,
        created_at=entry_date
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    if entry.attachments:
        for att in entry.attachments:
            db_att = models.Attachment(
                journal_entry_id=db_entry.id,
                file_path=att.file_path,
                filename=att.filename,
                media_type=att.media_type,
                created_at=date.today()
            )
            db.add(db_att)
        db.commit()
        db.refresh(db_entry)

    return db_entry

def update_journal_entry(db: Session, entry_id: int, entry: schemas.JournalEntryUpdate):
    db_entry = db.query(models.JournalEntry).filter(models.JournalEntry.id == entry_id).first()
    if not db_entry:
        return None
        
    update_data = entry.model_dump(exclude_unset=True)
    attachments_data = update_data.pop("attachments", None)

    for key, value in update_data.items():
        setattr(db_entry, key, value)

    # Note: attachments_data is a dict after model_dump(), while entry.attachments are Pydantic objects
    if attachments_data:
        for att in attachments_data:
            db_att = models.Attachment(
                journal_entry_id=db_entry.id,
                file_path=att['file_path'],
                filename=att['filename'],
                media_type=att['media_type'],
                created_at=date.today()
            )
            db.add(db_att)
        
    db.commit()
    db.refresh(db_entry)
    return db_entry

def delete_journal_entry(db: Session, entry_id: int):
    db_entry = db.query(models.JournalEntry).filter(models.JournalEntry.id == entry_id).first()
    if db_entry:
        db.delete(db_entry)
        db.commit()
        return True
    return False

# --- Material CRUD ---
def get_materials(db: Session):
    return db.query(models.Material).all()

def create_material(db: Session, material: schemas.MaterialCreate):
    db_material = models.Material(name=material.name)
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

def update_material(db: Session, material_id: int, name: str):
    db_material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not db_material:
        return None
    db_material.name = name
    db.commit()
    db.refresh(db_material)
    return db_material

def delete_material(db: Session, material_id: int):
    db_material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if db_material:
        db.delete(db_material)
        db.commit()
        return True
    return False

# --- Task CRUD ---
def get_tasks(db: Session, document_id: int):
    return db.query(models.Task).filter(models.Task.document_id == document_id).all()

def create_task(db: Session, document_id: int, task: schemas.TaskCreate):
    db_task = models.Task(
        document_id=document_id,
        name=task.name,
        status=task.status,
        assignee=task.assignee,
        material_id=task.material_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        return None
    update_data = task.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False

# --- Attachment CRUD ---
def delete_attachment(db: Session, attachment_id: int):
    db_att = db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()
    if db_att:
        # Delete physical file
        try:
             if db_att.file_path.startswith("/uploads/"):
                 filename = os.path.basename(db_att.file_path)
                 file_path = os.path.join("static/uploads", filename)
                 if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
             print(f"Error deleting file {db_att.file_path}: {e}")

        db.delete(db_att)
        db.commit()
        return True
    return False

# --- Filter Preset CRUD ---
def get_filter_presets(db: Session):
    return db.query(models.FilterPreset).all()

def create_filter_preset(db: Session, preset: schemas.FilterPresetCreate):
    db_preset = models.FilterPreset(name=preset.name, config=preset.config)
    db.add(db_preset)
    db.commit()
    db.refresh(db_preset)
    return db_preset

def delete_filter_preset(db: Session, preset_id: int):
    db_preset = db.query(models.FilterPreset).filter(models.FilterPreset.id == preset_id).first()
    if db_preset:
        db.delete(db_preset)
        db.commit()
        return True
    return False

# --- Part CRUD ---
def get_parts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    material_id: int | None = None,
    min_width: float | None = None,
    max_width: float | None = None,
    min_height: float | None = None,
    max_height: float | None = None
):
    query = db.query(models.Part).options(subqueryload(models.Part.material))
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(or_(
            models.Part.name.like(search_pattern),
            models.Part.registration_number.like(search_pattern)
        ))
    
    if material_id:
        query = query.filter(models.Part.material_id == material_id)
        
    if min_width is not None:
        query = query.filter(models.Part.width >= min_width)
    if max_width is not None:
        query = query.filter(models.Part.width <= max_width)
        
    if min_height is not None:
        query = query.filter(models.Part.height >= min_height)
    if max_height is not None:
        query = query.filter(models.Part.height <= max_height)
        
    return query.offset(skip).limit(limit).all()

def create_part(db: Session, part: schemas.PartCreate):
    db_part = models.Part(**part.model_dump())
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part

def update_part(db: Session, part_id: int, part_data: dict):
    db_part = db.query(models.Part).filter(models.Part.id == part_id).first()
    if not db_part:
        return None
    
    for key, value in part_data.items():
        if hasattr(db_part, key):
            setattr(db_part, key, value)
    
    db.commit()
    db.refresh(db_part)
    return db_part

def delete_part(db: Session, part_id: int):
    db_part = db.query(models.Part).filter(models.Part.id == part_id).first()
    if db_part:
        db.delete(db_part)
        db.commit()
        return True
    return False

# --- StockItem CRUD ---
def get_stock_items(db: Session):
    return db.query(models.StockItem).options(subqueryload(models.StockItem.material)).all()

def create_stock_item(db: Session, item: schemas.StockItemCreate):
    db_item = models.StockItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_stock_item(db: Session, item_id: int):
    db_item = db.query(models.StockItem).filter(models.StockItem.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False

# --- Workspace CRUD ---
def get_workspaces(db: Session):
    return db.query(models.Workspace).all()

def create_workspace(db: Session, ws: schemas.WorkspaceCreate):
    db_ws = models.Workspace(**ws.model_dump())
    db.add(db_ws)
    db.commit()
    db.refresh(db_ws)
    return db_ws

def delete_workspace(db: Session, ws_id: int):
    db_ws = db.query(models.Workspace).filter(models.Workspace.id == ws_id).first()
    if db_ws:
        db.delete(db_ws)
        db.commit()
        return True
    return False

# --- ShiftLog CRUD ---
def get_shift_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ShiftLog).order_by(models.ShiftLog.timestamp.desc()).offset(skip).limit(limit).all()

def create_shift_log(db: Session, log: schemas.ShiftLogCreate):
    db_log = models.ShiftLog(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# --- Reservation CRUD ---
def get_reservations(db: Session, task_id: int | None = None):
    query = db.query(models.Reservation)
    if task_id:
        query = query.filter(models.Reservation.task_id == task_id)
    return query.all()

def create_reservation(db: Session, reservation: schemas.ReservationCreate):
    db_res = models.Reservation(**reservation.model_dump())
    db.add(db_res)
    db.commit()
    db.refresh(db_res)
    return db_res

def delete_reservation(db: Session, reservation_id: int):
    db_res = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if db_res:
        db.delete(db_res)
        db.commit()
        return True
    return False

# --- Consumption CRUD ---
def get_consumptions(db: Session, task_id: int | None = None):
    query = db.query(models.Consumption)
    if task_id:
        query = query.filter(models.Consumption.task_id == task_id)
    return query.all()

def create_consumption(db: Session, consumption: schemas.ConsumptionCreate):
    db_cons = models.Consumption(**consumption.model_dump())
    db.add(db_cons)
    db.commit()
    db.refresh(db_cons)
    return db_cons

def delete_consumption(db: Session, consumption_id: int):
    db_cons = db.query(models.Consumption).filter(models.Consumption.id == consumption_id).first()
    if db_cons:
        db.delete(db_cons)
        db.commit()
        return True
    return False

# --- AuditLog CRUD ---
def get_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

def create_audit_log(db: Session, log: schemas.AuditLogCreate):
    db_log = models.AuditLog(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log
