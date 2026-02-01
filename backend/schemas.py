from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from .models import DocumentType, DocumentStatus, TaskStatus, JournalEntryType, JournalEntryStatus

# --- Filter Preset ---
class FilterPresetBase(BaseModel):
    name: str
    config: str

class FilterPresetCreate(FilterPresetBase):
    pass

class FilterPreset(FilterPresetBase):
    id: int

    class Config:
        from_attributes = True

# --- Tag ---
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int

    class Config:
        from_attributes = True

# --- Attachment ---
class AttachmentBase(BaseModel):
    file_path: str
    filename: str
    media_type: str
    created_at: Optional[date] = None

class AttachmentCreate(AttachmentBase):
    pass

class Attachment(AttachmentBase):
    id: int
    document_id: Optional[int] = None
    journal_entry_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Material ---
class MaterialBase(BaseModel):
    name: str

class MaterialCreate(MaterialBase):
    pass

class Material(MaterialBase):
    id: int

    class Config:
        from_attributes = True

# --- Task ---
class TaskBase(BaseModel):
    name: str
    status: TaskStatus = TaskStatus.PLANNED
    assignee: Optional[str] = None
    material_id: Optional[int] = None
    gnc_file_path: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[TaskStatus] = None
    assignee: Optional[str] = None
    material_id: Optional[int] = None
    gnc_file_path: Optional[str] = None

class Task(TaskBase):
    id: int
    document_id: int
    material: Optional[Material] = None

    class Config:
        from_attributes = True

# --- Journal (Forward Declaration for Document) ---
class JournalEntryBase(BaseModel):
    text: str
    type: JournalEntryType
    status: JournalEntryStatus
    author: Optional[str] = None
    document_id: Optional[int] = None
    created_at: Optional[date] = None

class JournalEntryCreate(JournalEntryBase):
    attachments: Optional[List[AttachmentCreate]] = []

class JournalEntryUpdate(BaseModel):
    text: Optional[str] = None
    type: Optional[JournalEntryType] = None
    status: Optional[JournalEntryStatus] = None
    author: Optional[str] = None
    document_id: Optional[int] = None
    attachments: Optional[List[AttachmentCreate]] = None

class JournalEntry(JournalEntryBase):
    id: int
    attachments: List[Attachment] = []
    # document: Optional['DocumentBase'] = None # Avoid circular dependency complexity if not strictly needed in list, or use specific schema

    class Config:
        from_attributes = True

# --- Document ---
class DocumentBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: DocumentType
    status: DocumentStatus
    registration_date: Optional[date] = None
    content: Optional[str] = None
    author: Optional[str] = None
    done_date: Optional[date] = None

class DocumentCreate(DocumentBase):
    attachments: Optional[List[AttachmentCreate]] = []
    tags: Optional[List[str]] = []

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    registration_date: Optional[date] = None
    content: Optional[str] = None
    author: Optional[str] = None
    done_date: Optional[date] = None
    attachments: Optional[List[AttachmentCreate]] = None
    tags: Optional[List[str]] = None

class Document(DocumentBase):
    id: int
    attachments: List[Attachment] = []
    tasks: List[Task] = []
    journal_entries: List[JournalEntry] = []
    tags: List[Tag] = []

    class Config:
        from_attributes = True

# --- Setting ---
class Setting(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True

# Update JournalEntry to have document info if needed (using DocumentBase to avoid recursion loop with Document.journal_entries)
class JournalEntryWithDoc(JournalEntry):
    document: Optional[DocumentBase] = None
