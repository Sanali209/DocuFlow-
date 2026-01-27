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
