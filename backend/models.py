from sqlalchemy import Column, Integer, String, Date, Enum, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
import enum
from datetime import date
from .database import Base

class DocumentType(str, enum.Enum):
    PLAN = "plan"
    MAIL = "mail"
    OTHER = "other"

class DocumentStatus(str, enum.Enum):
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

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    name = Column(String)
    status = Column(Enum(TaskStatus), default=TaskStatus.PLANNED)
    assignee = Column(String, nullable=True)

    document = relationship("Document", back_populates="tasks")

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
