from sqlalchemy import Column, Integer, String, Date, Enum, Text
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

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(Enum(DocumentType), default=DocumentType.OTHER)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.IN_PROGRESS)
    registration_date = Column(Date, default=date.today)
    content = Column(Text, nullable=True)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)

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
    document_id = Column(Integer, index=True, nullable=True) # Logical FK (SQLite weak enforcement by default)
    created_at = Column(Date, default=date.today)

