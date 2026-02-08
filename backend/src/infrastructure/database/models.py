from sqlalchemy import Column, Integer, String, Date, Enum, Text, ForeignKey, Table, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, datetime
import enum

Base = declarative_base()

# Association Table for Tags
document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class TagDB(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    documents = relationship("DocumentDB", secondary=document_tags, back_populates="tags")

class AttachmentDB(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    file_path = Column(String)
    filename = Column(String)
    media_type = Column(String)
    created_at = Column(Date, default=date.today)
    document = relationship("DocumentDB", back_populates="attachments")

class MaterialDB(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    tasks = relationship("TaskDB", back_populates="material")
    parts = relationship("PartDB", back_populates="material")
    stock_items = relationship("StockItemDB", back_populates="material")

class DocumentDB(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    type = Column(String) # Store enum as string
    status = Column(String) # Store enum as string
    registration_date = Column(Date, default=date.today)
    content = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    done_date = Column(Date, nullable=True)

    attachments = relationship("AttachmentDB", back_populates="document", cascade="all, delete-orphan")
    tasks = relationship("TaskDB", back_populates="document", cascade="all, delete-orphan")
    tags = relationship("TagDB", secondary=document_tags, back_populates="documents")

class TaskPartDB(Base):
    __tablename__ = "task_parts"
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    part_id = Column(Integer, ForeignKey("parts.id"), primary_key=True)
    quantity = Column(Integer, default=1)

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    name = Column(String)
    status = Column(String)
    assignee = Column(String, nullable=True)
    gnc_file_path = Column(String, nullable=True)

    document = relationship("DocumentDB", back_populates="tasks")
    material = relationship("MaterialDB", back_populates="tasks")
    parts = relationship("PartDB", secondary="task_parts")

class PartDB(Base):
    __tablename__ = "parts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    registration_number = Column(String, index=True)
    version = Column(String)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    gnc_file_path = Column(String, nullable=True)
    width = Column(Float, default=0.0)
    height = Column(Float, default=0.0)
    stats = Column(Text, nullable=True)

    material = relationship("MaterialDB", back_populates="parts")
class SettingDB(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)

class JournalEntryDB(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    type = Column(String)
    status = Column(String)
    author = Column(String, index=True, nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    created_at = Column(Date, default=date.today)

    document = relationship("DocumentDB", back_populates="journal_entries")
    attachments = relationship("AttachmentDB", back_populates="journal_entry")

class StockItemDB(Base):
    __tablename__ = "stock_items"
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    width = Column(Float)
    height = Column(Float)
    quantity = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
    location = Column(String, nullable=True)

    material = relationship("MaterialDB", back_populates="stock_items")

class ReservationDB(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"))
    quantity_reserved = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

class ConsumptionDB(Base):
    __tablename__ = "consumptions"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"))
    quantity_used = Column(Integer, default=0)
    remnants_created = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class AuditLogDB(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    actor = Column(String, nullable=True)
    action_type = Column(String)
    entity_type = Column(String)
    entity_id = Column(Integer, nullable=True)
    previous_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

class AssigneeDB(Base):
    __tablename__ = "assignees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class FilterPresetDB(Base):
    __tablename__ = "filter_presets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    config = Column(Text) # JSON string of filter settings

# Add missing relationships to DocumentDB
DocumentDB.journal_entries = relationship("JournalEntryDB", back_populates="document")
AttachmentDB.journal_entry = relationship("JournalEntryDB", back_populates="attachments")
