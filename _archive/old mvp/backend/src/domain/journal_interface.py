from abc import ABC, abstractmethod

from src.domain.models import JournalEntry


class IJournalRepository(ABC):
    @abstractmethod
    def get_by_id(self, entry_id: int) -> JournalEntry | None:
        pass

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> list[JournalEntry]:
        pass

    @abstractmethod
    def add(self, entity: JournalEntry) -> JournalEntry:
        pass

    @abstractmethod
    def delete(self, entry_id: int) -> bool:
        pass
