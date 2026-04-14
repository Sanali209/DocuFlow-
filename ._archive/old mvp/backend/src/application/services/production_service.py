import json

from src.domain.interfaces import IDocumentRepository, ITaskRepository
from src.domain.models import Document, Task


class ProductionService:
    def __init__(self, task_repo: ITaskRepository, doc_repo: IDocumentRepository):
        self.task_repo = task_repo
        self.doc_repo = doc_repo

    def list_jobs(self, skip: int = 0, limit: int = 100, filters: dict = None) -> list[Task]:
        return self.task_repo.list(skip, limit, filters)

    def get_job(self, id: int) -> Task | None:
        return self.task_repo.get_by_id(id)

    def create_job(self, task: Task) -> Task:
        return self.task_repo.add(task)

    def update_job(self, task: Task) -> Task:
        return self.task_repo.update(task)

    def delete_job(self, id: int) -> bool:
        return self.task_repo.delete(id)

    def update_job_status(self, id: int, status: str) -> Task | None:
        task = self.task_repo.get_by_id(id)
        if task:
            task.status = status
            return self.task_repo.update(task)
        return None

    def get_order_tasks(self, order_id: int) -> list[Task]:
        return self.task_repo.get_tasks_by_document_id(order_id)

    def save_nesting(self, order_id: int, project_data: dict) -> bool:
        doc = self.doc_repo.get_by_id(order_id)
        if doc:
            doc.content = json.dumps(project_data)
            self.doc_repo.update(doc)
            return True
        return False

    def get_nesting_project(self, order_id: int) -> dict | None:
        doc = self.doc_repo.get_by_id(order_id)
        if doc and doc.content:
            try:
                return json.loads(doc.content)
            except:
                return None
        return None

    def save_as_new_order(self, data: dict) -> Document:
        return self.doc_repo.save_as_new_order(data)
