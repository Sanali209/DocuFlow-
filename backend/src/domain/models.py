from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class DocumentType(str, Enum):
    PLAN = "plan"
    MAIL = "mail"
    ORDER = "order"
    PART = "part"
    OTHER = "other"

class DocumentStatus(str, Enum):
    UNREGISTERED = "unregistered"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskStatus(str, Enum):
    PLANNED = "planned"
    PENDING = "pending"
    DONE = "done"

class JournalEntryType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class JournalEntryStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"



class DomainModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class Tag(DomainModel):
    id: Optional[int] = None
    name: str

class Attachment(DomainModel):
    id: Optional[int] = None
    document_id: Optional[int] = None
    journal_entry_id: Optional[int] = None
    file_path: str
    filename: str
    media_type: str
    created_at: date = date.today()

class JournalEntry(DomainModel):
    id: Optional[int] = None
    text: str
    type: JournalEntryType = JournalEntryType.INFO
    status: JournalEntryStatus = JournalEntryStatus.PENDING
    author: Optional[str] = None
    document_id: Optional[int] = None
    created_at: datetime = datetime.now()
    attachments: List[Attachment] = []

class Material(DomainModel):
    id: Optional[int] = None
    name: str

class Assignee(DomainModel):
    id: Optional[int] = None
    name: str

class Part(DomainModel):
    id: Optional[int] = None
    name: str
    registration_number: str
    version: Optional[str] = "A"
    material_id: Optional[int] = None
    gnc_file_path: Optional[str] = None
    width: Optional[float] = 0.0
    height: Optional[float] = 0.0
    stats: Optional[str] = None

class StockItem(DomainModel):
    id: Optional[int] = None
    material_id: int
    width: Optional[float] = 0.0
    height: Optional[float] = 0.0
    quantity: int = 0
    reserved: int = 0
    location: Optional[str] = None

class Reservation(DomainModel):
    id: Optional[int] = None
    task_id: int
    stock_item_id: int
    quantity_reserved: int
    created_at: datetime = datetime.now()

class Consumption(DomainModel):
    id: Optional[int] = None
    task_id: int
    stock_item_id: int
    quantity_used: int
    remnants_created: bool = False
    created_at: datetime = datetime.now()

class Task(DomainModel):
    id: Optional[int] = None
    document_id: int
    material_id: Optional[int] = None
    name: str
    status: TaskStatus = TaskStatus.PLANNED
    assignee: Optional[str] = None
    gnc_file_path: Optional[str] = None
    material: Optional[Material] = None
    parts: List[Part] = []

class FilterPreset(DomainModel):
    id: Optional[int] = None
    name: str
    config: str # JSON string of filter settings

class Document(DomainModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    type: DocumentType = DocumentType.OTHER
    status: DocumentStatus = DocumentStatus.IN_PROGRESS
    registration_date: date = date.today()
    content: Optional[str] = None
    author: Optional[str] = None
    done_date: Optional[date] = None
    tags: List[Tag] = []
    attachments: List[Attachment] = []
    tasks: List[Task] = []
    journal_entries: List[JournalEntry] = []
