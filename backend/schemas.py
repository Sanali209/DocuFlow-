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

from .models import JournalEntryType, JournalEntryStatus

class JournalEntryBase(BaseModel):
    text: str
    type: JournalEntryType
    status: JournalEntryStatus
    author: str | None = None
    document_id: int | None = None
    created_at: date | None = None

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(BaseModel):
    text: str | None = None
    type: JournalEntryType | None = None
    status: JournalEntryStatus | None = None
    author: str | None = None
    document_id: int | None = None

class JournalEntry(JournalEntryBase):
    id: int

    class Config:
        from_attributes = True

