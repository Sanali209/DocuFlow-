from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import json
from typing import List, Optional
from src.domain.models import Document, Tag, Attachment, Task, Part, DocumentType, DocumentStatus, TaskStatus, FilterPreset
from src.domain.interfaces import IDocumentRepository, ITaskRepository
from .models import DocumentDB, TagDB, AttachmentDB, TaskDB, PartDB, MaterialDB, StockItemDB, JournalEntryDB, AuditLogDB, FilterPresetDB

class SQLDocumentRepository(IDocumentRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, db_doc: DocumentDB) -> Document:
        return Document(
            id=db_doc.id,
            name=db_doc.name,
            description=db_doc.description,
            type=db_doc.type.lower() if db_doc.type else DocumentType.OTHER,
            status=db_doc.status.lower() if db_doc.status else DocumentStatus.IN_PROGRESS,
            registration_date=db_doc.registration_date,
            content=db_doc.content,
            author=db_doc.author,
            done_date=db_doc.done_date,
            tags=[Tag(id=t.id, name=t.name) for t in db_doc.tags],
            attachments=[Attachment(
                id=a.id, 
                document_id=a.document_id,
                file_path=a.file_path,
                filename=a.filename,
                media_type=a.media_type,
                created_at=a.created_at
            ) for a in db_doc.attachments],
            tasks=[Task(
                id=t.id,
                document_id=t.document_id,
                material_id=t.material_id,
                name=t.name,
                status=t.status.lower() if t.status else TaskStatus.PLANNED,
                assignee=t.assignee,
                gnc_file_path=t.gnc_file_path,
                parts=[Part(id=p.id, name=p.name, registration_number=p.registration_number) for p in t.parts]
            ) for t in db_doc.tasks],
            journal_entries=[JournalEntry(
                id=j.id,
                text=j.text,
                type=j.type.lower() if j.type else "info",
                status=j.status.lower() if j.status else "pending",
                author=j.author,
                document_id=j.document_id,
                created_at=j.created_at,
                attachments=[Attachment(
                    id=a.id,
                    document_id=a.document_id,
                    journal_entry_id=a.journal_entry_id,
                    file_path=a.file_path,
                    filename=a.filename,
                    media_type=a.media_type,
                    created_at=a.created_at
                ) for a in j.attachments]
            ) for j in db_doc.journal_entries]
        )

    def get_by_id(self, document_id: int) -> Optional[Document]:
        db_doc = self.db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        return self._to_domain(db_doc) if db_doc else None

    def list(self, skip: int = 0, limit: int = 100) -> List[Document]:
        db_docs = self.db.query(DocumentDB).offset(skip).limit(limit).all()
        return [self._to_domain(d) for d in db_docs]

    def add(self, document: Document) -> Document:
        db_doc = DocumentDB(
            name=document.name,
            description=document.description,
            type=document.type,
            status=document.status.lower() if document.status else DocumentStatus.IN_PROGRESS,
            registration_date=document.registration_date,
            content=document.content,
            author=document.author,
            done_date=document.done_date
        )
        self.db.add(db_doc)
        self.db.commit()
        self.db.refresh(db_doc)
        return self._to_domain(db_doc)

    def update(self, document: Document) -> Document:
        db_doc = self.db.query(DocumentDB).filter(DocumentDB.id == document.id).first()
        if not db_doc:
            raise ValueError(f"Document with id {document.id} not found")
        
        db_doc.name = document.name
        db_doc.description = document.description
        db_doc.type = document.type.lower() if document.type else db_doc.type
        db_doc.status = document.status.lower() if document.status else db_doc.status
        db_doc.content = document.content
        db_doc.author = document.author
        db_doc.done_date = document.done_date
        
        self.db.commit()
        self.db.refresh(db_doc)
        return self._to_domain(db_doc)

    def delete(self, document_id: int) -> bool:
        db_doc = self.db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if db_doc:
            self.db.delete(db_doc)
            self.db.commit()
            return True
        return False

    def get_dashboard_stats(self) -> dict:
        # Document Stats
        total_docs = self.db.query(DocumentDB).count()
        doc_stats = self.db.query(func.lower(DocumentDB.status), func.count(DocumentDB.id)).group_by(func.lower(DocumentDB.status)).all()
        doc_by_status = {status: count for status, count in doc_stats}
        
        # Task Stats
        total_tasks = self.db.query(TaskDB).count()
        task_stats = self.db.query(func.lower(TaskDB.status), func.count(TaskDB.id)).group_by(func.lower(TaskDB.status)).all()
        task_by_status = {status: count for status, count in task_stats}
        
        assignee_stats = self.db.query(TaskDB.assignee, func.count(TaskDB.id)).group_by(TaskDB.assignee).all()
        task_by_assignee = {name if name else "Unassigned": count for name, count in assignee_stats}

        # Inventory Stats
        total_parts = self.db.query(PartDB).count()
        total_materials = self.db.query(MaterialDB).count()
        stock_metrics = self.db.query(
            func.sum(StockItemDB.quantity).label("total_qty"),
            func.sum(StockItemDB.reserved).label("total_res")
        ).first()

        # Journal Summary (Normalizing types)
        journal_stats = self.db.query(func.lower(JournalEntryDB.type), func.count(JournalEntryDB.id)).group_by(func.lower(JournalEntryDB.type)).all()
        journal_summary = {t: count for t, count in journal_stats}

        # Recent Activity (Last 10 Audit Logs)
        recent_logs = self.db.query(AuditLogDB).order_by(desc(AuditLogDB.timestamp)).limit(10).all()
        recent_activity = [
            {
                "actor": log.actor or "System",
                "action": log.action_type,
                "entity": log.entity_type,
                "entity_id": log.entity_id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            }
            for log in recent_logs
        ]
        
        return {
            "document_stats": {
                "total": total_docs,
                "by_status": doc_by_status
            },
            "task_stats": {
                "total": total_tasks,
                "by_status": task_by_status,
                "by_assignee": task_by_assignee
            },
            "inventory": {
                "total_parts": total_parts,
                "total_materials": total_materials,
                "total_quantity": stock_metrics.total_qty or 0 if stock_metrics else 0,
                "total_reserved": stock_metrics.total_res or 0 if stock_metrics else 0
            },
            "journal_summary": journal_summary,
            "recent_activity": recent_activity
        }

    def delete_attachment(self, attachment_id: int) -> bool:
        db_att = self.db.query(AttachmentDB).filter(AttachmentDB.id == attachment_id).first()
        if db_att:
            self.db.delete(db_att)
            self.db.commit()
            return True
        return False

    def get_attachment(self, attachment_id: int) -> Optional[dict]:
        db_att = self.db.query(AttachmentDB).filter(AttachmentDB.id == attachment_id).first()
        if db_att:
            return {
                "id": db_att.id,
                "document_id": db_att.document_id,
                "file_path": db_att.file_path,
                "filename": db_att.filename
            }
        return None

    def create_order(self, name: str, items: List[dict]) -> Document:
        db_doc = DocumentDB(
            name=name,
            type=DocumentType.ORDER,
            status=DocumentStatus.IN_PROGRESS
        )
        self.db.add(db_doc)
        self.db.flush()
        
        for item in items:
            db_task = TaskDB(
                document_id=db_doc.id,
                name=f"Produce Part ID: {item['id']}",
                status=TaskStatus.PLANNED
            )
            self.db.add(db_task)
            
        self.db.commit()
        self.db.refresh(db_doc)
        return self._to_domain(db_doc)

    def list_tags(self) -> List[Tag]:
        db_tags = self.db.query(TagDB).all()
        return [Tag(id=t.id, name=t.name) for t in db_tags]

    def save_as_new_order(self, data: dict) -> Document:
        db_doc = DocumentDB(
            name=data["name"],
            type=DocumentType.ORDER,
            status=DocumentStatus.IN_PROGRESS,
            content=json.dumps(data.get("sheets", []))
        )
        self.db.add(db_doc)
        self.db.commit()
        self.db.refresh(db_doc)
        return self._to_domain(db_doc)

class SQLTaskRepository(ITaskRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, db_task: TaskDB) -> Task:
        return Task(
            id=db_task.id,
            document_id=db_task.document_id,
            material_id=db_task.material_id,
            name=db_task.name,
            assignee=db_task.assignee,
            gnc_file_path=db_task.gnc_file_path,
            material=Material(id=db_task.material.id, name=db_task.material.name) if db_task.material else None,
            parts=[Part(id=p.id, name=p.name, registration_number=p.registration_number) for p in db_task.parts]
        )

    def get_by_id(self, task_id: int) -> Optional[Task]:
        db_task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        return self._to_domain(db_task) if db_task else None

    def list(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[Task]:
        query = self.db.query(TaskDB)
        if filters:
            if filters.get("assignee"):
                query = query.filter(TaskDB.assignee.ilike(f"%{filters['assignee']}%"))
            if filters.get("status"):
                query = query.filter(TaskDB.status == filters["status"])
        db_tasks = query.offset(skip).limit(limit).all()
        return [self._to_domain(t) for t in db_tasks]

    def add(self, task: Task) -> Task:
        db_task = TaskDB(
            document_id=task.document_id,
            material_id=task.material_id,
            name=task.name,
            status=(task.status or TaskStatus.PLANNED).lower(),
            assignee=task.assignee,
            gnc_file_path=task.gnc_file_path
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return self._to_domain(db_task)

    def update(self, task: Task) -> Task:
        db_task = self.db.query(TaskDB).filter(TaskDB.id == task.id).first()
        if not db_task:
            raise ValueError(f"Task with id {task.id} not found")
        
        db_task.name = task.name
        db_task.status = task.status.lower() if task.status else db_task.status
        db_task.assignee = task.assignee
        db_task.gnc_file_path = task.gnc_file_path
        db_task.material_id = task.material_id
        
        self.db.commit()
        self.db.refresh(db_task)
        return self._to_domain(db_task)

    def delete(self, task_id: int) -> bool:
        db_task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if db_task:
            self.db.delete(db_task)
            self.db.commit()
            return True
        return False

    def get_tasks_by_document_id(self, document_id: int) -> List[Task]:
        db_tasks = self.db.query(TaskDB).filter(TaskDB.document_id == document_id).all()
        return [self._to_domain(t) for t in db_tasks]

class SQLFilterPresetRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, db_preset: FilterPresetDB) -> FilterPreset:
        return FilterPreset(
            id=db_preset.id,
            name=db_preset.name,
            config=db_preset.config
        )

    def list(self) -> List[FilterPreset]:
        db_presets = self.db.query(FilterPresetDB).all()
        return [self._to_domain(p) for p in db_presets]

    def add(self, name: str, config: str) -> FilterPreset:
        db_preset = FilterPresetDB(name=name, config=config)
        self.db.add(db_preset)
        self.db.commit()
        self.db.refresh(db_preset)
        return self._to_domain(db_preset)

    def delete(self, preset_id: int) -> bool:
        db_preset = self.db.query(FilterPresetDB).filter(FilterPresetDB.id == preset_id).first()
        if db_preset:
            self.db.delete(db_preset)
            self.db.commit()
            return True
        return False
