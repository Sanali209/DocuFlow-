from sqlalchemy.orm import Session
from . import models, schemas
from datetime import date

def get_documents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search_name: str | None = None,
    filter_type: models.DocumentType | None = None,
    filter_status: models.DocumentStatus | None = None
):
    query = db.query(models.Document)

    if search_name:
        query = query.filter(models.Document.name.contains(search_name))

    if filter_type:
        query = query.filter(models.Document.type == filter_type)

    if filter_status:
        query = query.filter(models.Document.status == filter_status)

    return query.offset(skip).limit(limit).all()

def create_document(db: Session, document: schemas.DocumentCreate):
    # Set default date if not provided
    reg_date = document.registration_date if document.registration_date else date.today()

    db_document = models.Document(
        name=document.name,
        type=document.type,
        status=document.status,
        registration_date=reg_date,
        content=document.content
    )
    db.add(db_document)
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
    for key, value in update_data.items():
        setattr(db_document, key, value)

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
    query = db.query(models.JournalEntry)
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
    return db_entry

def update_journal_entry(db: Session, entry_id: int, entry: schemas.JournalEntryUpdate):
    db_entry = db.query(models.JournalEntry).filter(models.JournalEntry.id == entry_id).first()
    if not db_entry:
        return None
        
    update_data = entry.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_entry, key, value)
        
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
