from typing import List, Optional
from src.domain.models import JournalEntry, Attachment
from abc import ABC, abstractmethod

class IJournalRepository(ABC):
    @abstractmethod
    def get_by_id(self, entry_id: int) -> Optional[JournalEntry]:
        pass

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> List[JournalEntry]:
        pass

    @abstractmethod
    def add(self, entity: JournalEntry) -> JournalEntry:
        pass

    @abstractmethod
    def delete(self, entry_id: int) -> bool:
        pass
