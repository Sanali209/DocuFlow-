import os
from typing import List, Optional
from src.domain.models import Document, Tag
from src.domain.interfaces import IDocumentRepository

class DocumentService:
    def __init__(self, doc_repo: IDocumentRepository):
        self.doc_repo = doc_repo

    def get_document(self, document_id: int) -> Optional[Document]:
        # business logic can go here (e.g. tracking, permission check)
        return self.doc_repo.get_by_id(document_id)

    def list_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        return self.doc_repo.list(skip=skip, limit=limit)

    def create_document(self, document: Document) -> Document:
        # business logic: validation, default values, side effects
        return self.doc_repo.add(document)

    def update_document(self, document: Document) -> Document:
        return self.doc_repo.update(document)

    def delete_document(self, document_id: int) -> bool:
        return self.doc_repo.delete(document_id)

    def create_order(self, name: str, items: List[dict]) -> Document:
        return self.doc_repo.create_order(name, items)

    def save_as_new_order(self, data: dict) -> Document:
        return self.doc_repo.save_as_new_order(data)

    def list_tags(self) -> List[Tag]:
        return self.doc_repo.list_tags()

    def get_dashboard_stats(self) -> dict:
        return self.doc_repo.get_dashboard_stats()

    def delete_attachment(self, attachment_id: int) -> bool:
        return self.doc_repo.delete_attachment(attachment_id)

    def get_document_zip(self, document_id: int):
        doc = self.doc_repo.get_by_id(document_id)
        if not doc or not doc.attachments:
            return None
            
        first_att = doc.attachments[0]
        folder = os.path.dirname(first_att.file_path)
        
        from src.infrastructure.zip_util import create_folder_zip
        try:
            return create_folder_zip(folder)
        except Exception:
            return None
