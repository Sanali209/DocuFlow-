from sqlalchemy import Column, Integer, String, Date, Enum, Text, ForeignKey, Table, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import date, datetime
from .database import Base

class DocumentType(str, enum.Enum):
    PLAN = "plan"
    MAIL = "mail"
    ORDER = "order"
    PART = "part"
    OTHER = "other"

class DocumentStatus(str, enum.Enum):
    UNREGISTERED = "unregistered"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskStatus(str, enum.Enum):
    PLANNED = "planned"
    PENDING = "pending"
    DONE = "done"

# Association Table for Tags
document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    documents = relationship("Document", secondary=document_tags, back_populates="tags")

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    file_path = Column(String)
    filename = Column(String)
    media_type = Column(String)
    created_at = Column(Date, default=date.today)

    document = relationship("Document", back_populates="attachments")
    journal_entry = relationship("JournalEntry", back_populates="attachments")

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    tasks = relationship("Task", back_populates="material")
    parts = relationship("Part", back_populates="material")
    tasks = relationship("Task", back_populates="material")
    tasks = relationship("Task", back_populates="material")
    parts = relationship("Part", back_populates="material")
    stock_items = relationship("StockItem", back_populates="material")

class Assignee(Base):
    __tablename__ = "assignees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

# Association Table for Task-Parts
task_parts = Table(
    "task_parts",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("part_id", Integer, ForeignKey("parts.id"), primary_key=True),
)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    name = Column(String)
    status = Column(Enum(TaskStatus), default=TaskStatus.PLANNED)
    assignee = Column(String, nullable=True)
    gnc_file_path = Column(String, nullable=True)

    document = relationship("Document", back_populates="tasks")
    material = relationship("Material", back_populates="tasks")
    reservations = relationship("Reservation", back_populates="task", cascade="all, delete-orphan")
    consumptions = relationship("Consumption", back_populates="task", cascade="all, delete-orphan")
    parts = relationship("Part", secondary=task_parts, back_populates="tasks")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    type = Column(Enum(DocumentType), default=DocumentType.OTHER)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.IN_PROGRESS)
    registration_date = Column(Date, default=date.today)
    content = Column(Text, nullable=True)

    author = Column(String, nullable=True)
    done_date = Column(Date, nullable=True)

    attachments = relationship("Attachment", back_populates="document", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="document", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="document")
    tags = relationship("Tag", secondary=document_tags, back_populates="documents")

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)

class FilterPreset(Base):
    __tablename__ = "filter_presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    config = Column(Text) # JSON string

class JournalEntryType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class JournalEntryStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    type = Column(Enum(JournalEntryType), default=JournalEntryType.INFO)
    status = Column(Enum(JournalEntryStatus), default=JournalEntryStatus.PENDING)
    author = Column(String, index=True, nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    created_at = Column(Date, default=date.today)

    document = relationship("Document", back_populates="journal_entries")
    attachments = relationship("Attachment", back_populates="journal_entry", cascade="all, delete-orphan")

# Association Table for Task-Parts

class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    registration_number = Column(String, index=True)
    version = Column(String) # A, B, C
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    gnc_file_path = Column(String, nullable=True)

    # Dimensions
    width = Column(Float, default=0.0)
    height = Column(Float, default=0.0)

    # Stats (JSON stored as text)
    stats = Column(Text, nullable=True)

    material = relationship("Material", back_populates="parts")
    tasks = relationship("Task", secondary=task_parts, back_populates="parts")

class StockItem(Base):
    __tablename__ = "stock_items"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    width = Column(Float)
    height = Column(Float)
    quantity = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
    location = Column(String, nullable=True)

    material = relationship("Material", back_populates="stock_items")
    reservations = relationship("Reservation", back_populates="stock_item")
    consumptions = relationship("Consumption", back_populates="stock_item")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"))
    quantity_reserved = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    task = relationship("Task", back_populates="reservations")
    stock_item = relationship("StockItem", back_populates="reservations")

class Consumption(Base):
    __tablename__ = "consumptions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"))
    quantity_used = Column(Integer, default=0)
    remnants_created = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    task = relationship("Task", back_populates="consumptions")
    stock_item = relationship("StockItem", back_populates="consumptions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    actor = Column(String, nullable=True)
    action_type = Column(String) # CREATE, UPDATE, DELETE
    entity_type = Column(String)
    entity_id = Column(Integer, nullable=True)
    previous_value = Column(Text, nullable=True) # JSON
    new_value = Column(Text, nullable=True) # JSON

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)
    capabilities = Column(Text, nullable=True) # JSON
    status = Column(String, default="active")


