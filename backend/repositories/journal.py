from sqlalchemy.orm import Session
from datetime import date
from .. import models, schemas

def get_journal_entries(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filter_type: models.JournalEntryType | None = None,
    filter_status: models.JournalEntryStatus | None = None,
    filter_date: date | None = None,
    document_id: int | None = None
):
    query = db.query(models.JournalEntry)
    if filter_type:
        query = query.filter(models.JournalEntry.type == filter_type)
    if filter_status:
        query = query.filter(models.JournalEntry.status == filter_status)
    if filter_date:
        query = query.filter(models.JournalEntry.created_at == filter_date)
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
