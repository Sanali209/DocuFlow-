from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models import Document, Part, Material, Task, Tag

class IDocumentRepository(ABC):
    @abstractmethod
    def get_by_id(self, document_id: int) -> Optional[Document]:
        pass

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> List[Document]:
        pass

    @abstractmethod
    def add(self, document: Document) -> Document:
        pass

    @abstractmethod
    def update(self, document: Document) -> Document:
        pass

    @abstractmethod
    def delete(self, document_id: int) -> bool:
        pass

    @abstractmethod
    def get_dashboard_stats(self) -> dict:
        pass

    @abstractmethod
    def delete_attachment(self, attachment_id: int) -> bool:
        pass
        
    @abstractmethod
    def get_attachment(self, attachment_id: int) -> Optional[dict]:
        pass

    @abstractmethod
    def create_order(self, name: str, items: List[dict]) -> Document:
        pass

    @abstractmethod
    def list_tags(self) -> List[Tag]:
        pass

    @abstractmethod
    def save_as_new_order(self, data: dict) -> Document:
        pass

class IPartRepository(ABC):
    @abstractmethod
    def get_by_id(self, part_id: int) -> Optional[Part]:
        pass

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> List[Part]:
        pass

    @abstractmethod
    def add(self, part: Part) -> Part:
        pass

class ITaskRepository(ABC):
    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[Task]: pass
    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> List[Task]: pass
    @abstractmethod
    def add(self, task: Task) -> Task: pass
    @abstractmethod
    def update(self, task: Task) -> Task: pass
    @abstractmethod
    def delete(self, task_id: int) -> bool: pass
    @abstractmethod
    def get_tasks_by_document_id(self, document_id: int) -> List[Task]: pass
