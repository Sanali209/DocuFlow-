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
