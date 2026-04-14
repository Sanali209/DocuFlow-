from datetime import date, datetime
from enum import Enum

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
    id: int | None = None
    name: str


class Attachment(DomainModel):
    id: int | None = None
    document_id: int | None = None
    journal_entry_id: int | None = None
    file_path: str
    filename: str
    media_type: str
    created_at: date = date.today()


class JournalEntry(DomainModel):
    id: int | None = None
    text: str
    type: JournalEntryType = JournalEntryType.INFO
    status: JournalEntryStatus = JournalEntryStatus.PENDING
    author: str | None = None
    document_id: int | None = None
    created_at: datetime = datetime.now()
    attachments: list[Attachment] = []


class Material(DomainModel):
    id: int | None = None
    name: str


class Assignee(DomainModel):
    id: int | None = None
    name: str


class Part(DomainModel):
    id: int | None = None
    name: str
    registration_number: str
    version: str | None = "A"
    material_id: int | None = None
    gnc_file_path: str | None = None
    width: float | None = 0.0
    height: float | None = 0.0
    stats: str | None = None


class StockItem(DomainModel):
    id: int | None = None
    material_id: int
    width: float | None = 0.0
    height: float | None = 0.0
    quantity: int = 0
    reserved: int = 0
    location: str | None = None


class Reservation(DomainModel):
    id: int | None = None
    task_id: int
    stock_item_id: int
    quantity_reserved: int
    created_at: datetime = datetime.now()


class Consumption(DomainModel):
    id: int | None = None
    task_id: int
    stock_item_id: int
    quantity_used: int
    remnants_created: bool = False
    created_at: datetime = datetime.now()


class Task(DomainModel):
    id: int | None = None
    document_id: int
    material_id: int | None = None
    name: str
    status: TaskStatus = TaskStatus.PLANNED
    # assignee: Optional[str] = None # REMOVED
    gnc_file_path: str | None = None
    material: Material | None = None
    parts: list[Part] = []
    assignees: list[Assignee] = []  # NEW


class FilterPreset(DomainModel):
    id: int | None = None
    name: str
    config: str  # JSON string of filter settings


class Document(DomainModel):
    id: int | None = None
    name: str
    description: str | None = None
    type: DocumentType = DocumentType.OTHER
    status: DocumentStatus = DocumentStatus.IN_PROGRESS
    registration_date: date = date.today()
    content: str | None = None
    author: str | None = None
    done_date: date | None = None
    tags: list[Tag] = []
    attachments: list[Attachment] = []
    tasks: list[Task] = []
    journal_entries: list[JournalEntry] = []
