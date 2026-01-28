from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, or_
from . import models, schemas
from datetime import date

def get_documents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search_name: str | None = None,
    filter_type: models.DocumentType | None = None,
    filter_status: models.DocumentStatus | None = None,
    sort_by: str = "registration_date",
    sort_order: str = "desc"
):
    query = db.query(models.Document).options(
        joinedload(models.Document.tasks),
        joinedload(models.Document.journal_entries),
        joinedload(models.Document.attachments)
    )

    if search_name:
        search_pattern = f"%{search_name}%"
        query = query.filter(or_(
            models.Document.name.like(search_pattern),
            models.Document.description.like(search_pattern),
            models.Document.content.like(search_pattern)
        ))

    if filter_type:
        query = query.filter(models.Document.type == filter_type)

    if filter_status:
        query = query.filter(models.Document.status == filter_status)

    # Sorting
    if hasattr(models.Document, sort_by):
        column = getattr(models.Document, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
    else:
        query = query.order_by(desc(models.Document.registration_date))

    # Use distinct if needed or rely on python-side unique for joinedload
    # SQLAlchemy joinedload with one-to-many can produce dupes in SQL result,
    # but the ORM usually uniques them if identity map is used.
    # However, limit/offset with joinedload is tricky.
    # It's better to subquery or rely on unique().
    # But Query.unique() method might be version dependent or deprecated in 2.0 style?
    # In 1.4/2.0 transition, .unique() is on Result, not Query.
    # But here we return .all().
    # Let's try .distinct() on the query if we weren't doing joinedload, but joinedload breaks distinct sometimes.

    # Correct approach for limit/offset with to-many joins:
    # 1. Query IDs with limit/offset
    # 2. Query full objects with those IDs

    # Or, since we are using joinedload, we can just use .unique() on the result execution if possible.
    # But `query.unique()` doesn't exist on legacy Query object in some versions?
    # Actually, `query.distinct()` is SQL DISTINCT.

    # Let's try removing .unique() and seeing if joinedload handles it, or using explicit subquery.
    # For simplicity in this app, let's just return .all() and let SQLAlchemy uniquify in memory
    # (which it does for joinedload collections).
    # BUT, if the main rows are duplicated, limit/offset counts rows, not objects.
    # So 1 doc with 5 tasks = 5 rows. Limit 10 = 2 docs.
    # This is a classic ORM problem.
    # Given the scale, I will switch to `selectinload` if possible (async recommended) or separate queries.
    # Or just remove joinedload and let lazy loading happen (N+1), which is fine for small apps.
    # But I want to avoid N+1.

    # Let's remove joinedload from the main query logic and rely on lazy loading for now,
    # OR change to `subqueryload`.

    # Actually, `unique()` IS available on Query in 1.4+, but maybe not in the installed version or I'm using it wrong.
    # Let's switch to `subqueryload` - it's safer for pagination.
    from sqlalchemy.orm import subqueryload

    query = db.query(models.Document).options(
        subqueryload(models.Document.tasks),
        subqueryload(models.Document.journal_entries),
        subqueryload(models.Document.attachments)
    )

    if search_name:
        search_pattern = f"%{search_name}%"
        query = query.filter(or_(
            models.Document.name.like(search_pattern),
            models.Document.description.like(search_pattern),
            models.Document.content.like(search_pattern)
        ))

    if filter_type:
        query = query.filter(models.Document.type == filter_type)

    if filter_status:
        query = query.filter(models.Document.status == filter_status)

    if hasattr(models.Document, sort_by):
        column = getattr(models.Document, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
    else:
        query = query.order_by(desc(models.Document.registration_date))

    return query.offset(skip).limit(limit).all()

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

    for key, value in update_data.items():
        setattr(db_document, key, value)

    if attachments_data:
        for att in attachments_data:
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

def delete_document(db: Session, document_id: int):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_document:
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
    query = db.query(models.JournalEntry).options(joinedload(models.JournalEntry.attachments))
    if filter_type:
        query = query.filter(models.JournalEntry.type == filter_type)
    if filter_status:
        query = query.filter(models.JournalEntry.status == filter_status)
    if document_id:
        query = query.filter(models.JournalEntry.document_id == document_id)
        
    return query.order_by(models.JournalEntry.created_at.desc()).offset(skip).limit(limit).unique().all()

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

    if attachments_data:
        for att in attachments_data:
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

def delete_journal_entry(db: Session, entry_id: int):
    db_entry = db.query(models.JournalEntry).filter(models.JournalEntry.id == entry_id).first()
    if db_entry:
        db.delete(db_entry)
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
        assignee=task.assignee
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
        db.delete(db_att)
        db.commit()
        return True
    return False
