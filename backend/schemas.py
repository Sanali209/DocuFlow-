from pydantic import BaseModel
from datetime import date
from .models import DocumentType, DocumentStatus

class DocumentBase(BaseModel):
    name: str
    type: DocumentType
    status: DocumentStatus
    registration_date: date | None = None
    content: str | None = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    name: str | None = None
    type: DocumentType | None = None
    status: DocumentStatus | None = None
    registration_date: date | None = None
    content: str | None = None

class Document(DocumentBase):
    id: int

    class Config:
        from_attributes = True

class Setting(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True
