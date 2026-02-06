from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional
from .models import DocumentType, DocumentStatus, TaskStatus, JournalEntryType, JournalEntryStatus

# --- Filter Preset ---
class PathCheck(BaseModel):
    path: str

class FilterPresetBase(BaseModel):
    name: str
    config: str

class FilterPresetCreate(FilterPresetBase):
    pass

class FilterPreset(FilterPresetBase):
    id: int

    class Config:
        from_attributes = True

# --- Reservation ---
class ReservationBase(BaseModel):
    task_id: int
    stock_item_id: int
    quantity_reserved: int

class ReservationCreate(ReservationBase):
    pass

class Reservation(ReservationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Consumption ---
class ConsumptionBase(BaseModel):
    task_id: int
    stock_item_id: int
    quantity_used: int
    remnants_created: bool = False

class ConsumptionCreate(ConsumptionBase):
    pass

class Consumption(ConsumptionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- AuditLog ---
class AuditLogBase(BaseModel):
    actor: Optional[str] = None
    action_type: str
    entity_type: str
    entity_id: Optional[int] = None
    previous_value: Optional[str] = None
    new_value: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime

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

# --- Assignee ---
class AssigneeBase(BaseModel):
    name: str

class AssigneeCreate(AssigneeBase):
    pass

class AssigneeUpdate(AssigneeBase):
    pass

class Assignee(AssigneeBase):
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
    material: Optional[Material] = None
    parts: List['Part'] = [] # Backward compatibility: returns List[Part] objects
    part_associations: List['TaskPartLink'] = [] # Returns association objects with quantity

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

class DatabaseConfig(BaseModel):
    database_path: str

# Update JournalEntry to have document info if needed (using DocumentBase to avoid recursion loop with Document.journal_entries)
class JournalEntryWithDoc(JournalEntry):
    document: Optional[DocumentBase] = None

# --- Part ---
class PartBase(BaseModel):
    name: str
    registration_number: str
    version: Optional[str] = "A"
    material_id: Optional[int] = None
    gnc_file_path: Optional[str] = None
    width: Optional[float] = 0.0
    height: Optional[float] = 0.0
    stats: Optional[str] = None

class PartCreate(PartBase):
    pass

class Part(PartBase):
    id: int
    material: Optional[Material] = None

    class Config:
        from_attributes = True

# --- TaskPart Link ---
class TaskPartLink(BaseModel):
    part_id: int
    quantity: int
    part: Part # Nested part details

    class Config:
        from_attributes = True

# --- StockItem ---
class StockItemBase(BaseModel):
    material_id: int
    width: float
    height: float
    quantity: int = 0
    reserved: int = 0
    location: Optional[str] = None

class StockItemCreate(StockItemBase):
    pass

class StockItem(StockItemBase):
    id: int
    material: Optional[Material] = None

    class Config:
        from_attributes = True

# --- Workspace ---
class WorkspaceBase(BaseModel):
    name: str
    type: str
    capabilities: Optional[str] = None
    status: str = "active"

class WorkspaceCreate(WorkspaceBase):
    pass

class Workspace(WorkspaceBase):
    id: int

    class Config:
        from_attributes = True


# --- Orders ---
class OrderItem(BaseModel):
    id: int # Part ID
    qty: int

class OrderCreate(BaseModel):
    name: str # Order Name
    parts: List[OrderItem]

# --- GNC Project & Multi-Sheet Nesting ---
from .gnc_parser import GNCSheet # We use the parser model as base for sheets

class GNCStockItem(BaseModel):
    id: int
    name: str
    width: float
    height: float
    material: Optional[str] = None
    quantity: int = 1

class GNCProjectSheet(BaseModel):
    id: int
    data: GNCSheet
    name: str

class GNCProject(BaseModel):
    order_id: Optional[int] = None
    name: str
    sheets: List[GNCProjectSheet] = []
    inventory: List[Task] = [] # Tasks/Parts to be placed
    stock: List[GNCStockItem] = [] # Local stock available for this session

class GNCProjectUpdate(BaseModel):
    order_id: int
    sheets: List[GNCProjectSheet]
