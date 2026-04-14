import builtins
from abc import ABC, abstractmethod
from datetime import date

from src.domain.models import Document, Part, Tag, Task


class IDocumentRepository(ABC):
    @abstractmethod
    def get_by_id(self, document_id: int) -> Document | None:
        pass

    @abstractmethod
    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        type: str = None,
        status: str = None,
        tag: str = None,
        assignee: str = None,
        material_id: int = None,
        part_search: str = None,
        sort_by: str = "registration_date",
        sort_order: str = "desc",
        start_date: date = None,
        end_date: date = None,
        date_field: str = "registration_date",
    ) -> list[Document]:
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
    def get_attachment(self, attachment_id: int) -> dict | None:
        pass

    @abstractmethod
    def create_order(self, name: str, items: builtins.list[dict]) -> Document:
        pass

    @abstractmethod
    def list_tags(self) -> builtins.list[Tag]:
        pass

    @abstractmethod
    def save_as_new_order(self, data: dict) -> Document:
        pass


class IPartRepository(ABC):
    @abstractmethod
    def get_by_id(self, part_id: int) -> Part | None:
        pass

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> list[Part]:
        pass

    @abstractmethod
    def add(self, part: Part) -> Part:
        pass


class ITaskRepository(ABC):
    @abstractmethod
    def get_by_id(self, task_id: int) -> Task | None:
        pass

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> list[Task]:
        pass

    @abstractmethod
    def add(self, task: Task) -> Task:
        pass

    @abstractmethod
    def update(self, task: Task) -> Task:
        pass

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        pass

    @abstractmethod
    def get_tasks_by_document_id(self, document_id: int) -> builtins.list[Task]:
        pass
