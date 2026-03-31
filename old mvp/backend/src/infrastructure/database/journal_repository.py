from sqlalchemy.orm import Session, subqueryload
from typing import List, Optional
from src.domain.models import JournalEntry, Attachment
from src.domain.journal_interface import IJournalRepository
from .models import JournalEntryDB, AttachmentDB

class SQLJournalRepository(IJournalRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, db_entry: JournalEntryDB) -> JournalEntry:
        return JournalEntry(
            id=db_entry.id,
            text=db_entry.text,
            type=db_entry.type,
            status=db_entry.status,
            author=db_entry.author,
            document_id=db_entry.document_id,
            created_at=db_entry.created_at,
            attachments=[Attachment(
                id=a.id,
                file_path=a.file_path,
                filename=a.filename,
                media_type=a.media_type,
                created_at=a.created_at
            ) for a in db_entry.attachments]
        )

    def get_by_id(self, entry_id: int) -> Optional[JournalEntry]:
        db_entry = self.db.query(JournalEntryDB).options(subqueryload(JournalEntryDB.attachments)).filter(JournalEntryDB.id == entry_id).first()
        return self._to_domain(db_entry) if db_entry else None

    def list(self, skip: int = 0, limit: int = 100) -> List[JournalEntry]:
        db_entries = self.db.query(JournalEntryDB).options(subqueryload(JournalEntryDB.attachments)).order_by(JournalEntryDB.created_at.desc()).offset(skip).limit(limit).all()
        return [self._to_domain(e) for e in db_entries]

    def add(self, entity: JournalEntry) -> JournalEntry:
        db_entry = JournalEntryDB(
            text=entity.text,
            type=entity.type,
            status=entity.status,
            author=entity.author,
            document_id=entity.document_id,
            created_at=entity.created_at
        )
        self.db.add(db_entry)
        self.db.commit()
        self.db.refresh(db_entry)
        return self._to_domain(db_entry)

    def delete(self, entry_id: int) -> bool:
        db_entry = self.db.query(JournalEntryDB).filter(JournalEntryDB.id == entry_id).first()
        if db_entry:
            self.db.delete(db_entry)
            self.db.commit()
            return True
        return False
