from typing import List, Optional
from src.domain.models import JournalEntry
from src.domain.journal_interface import IJournalRepository

class JournalService:
    def __init__(self, journal_repo: IJournalRepository):
        self.journal_repo = journal_repo

    def get_entry(self, entry_id: int) -> Optional[JournalEntry]:
        return self.journal_repo.get_by_id(entry_id)

    def list_entries(self, skip: int = 0, limit: int = 100) -> List[JournalEntry]:
        return self.journal_repo.list(skip, limit)

    def create_entry(self, entry: JournalEntry) -> JournalEntry:
        return self.journal_repo.add(entry)

    def delete_entry(self, entry_id: int) -> bool:
        return self.journal_repo.delete(entry_id)
