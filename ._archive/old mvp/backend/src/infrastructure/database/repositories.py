import builtins
import json
import os
from datetime import date

from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from src.domain.interfaces import IDocumentRepository, ITaskRepository
from src.domain.models import (
    Assignee,
    Attachment,
    Document,
    DocumentStatus,
    DocumentType,
    FilterPreset,
    JournalEntry,
    Material,
    Part,
    Tag,
    Task,
    TaskStatus,
)

from .models import (
    AssigneeDB,
    AttachmentDB,
    AuditLogDB,
    DocumentDB,
    FilterPresetDB,
    JournalEntryDB,
    MaterialDB,
    PartDB,
    StockItemDB,
    TagDB,
    TaskDB,
)


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
            attachments=[
                Attachment(
                    id=a.id,
                    document_id=a.document_id,
                    file_path=a.file_path,
                    filename=a.filename,
                    media_type=a.media_type,
                    created_at=a.created_at,
                )
                for a in db_doc.attachments
            ],
            tasks=[
                Task(
                    id=t.id,
                    document_id=t.document_id,
                    material_id=t.material_id,
                    name=t.name,
                    status=t.status.lower() if t.status else TaskStatus.PLANNED,
                    # assignee=t.assignee, # REMOVED
                    assignees=[Assignee(id=a.id, name=a.name) for a in t.assignees],
                    gnc_file_path=t.gnc_file_path,
                    parts=[
                        Part(id=p.id, name=p.name, registration_number=p.registration_number)
                        for p in t.parts
                    ],
                )
                for t in db_doc.tasks
            ],
            journal_entries=[
                JournalEntry(
                    id=j.id,
                    text=j.text,
                    type=j.type.lower() if j.type else "info",
                    status=j.status.lower() if j.status else "pending",
                    author=j.author,
                    document_id=j.document_id,
                    created_at=j.created_at,
                    attachments=[
                        Attachment(
                            id=a.id,
                            document_id=a.document_id,
                            journal_entry_id=a.journal_entry_id,
                            file_path=a.file_path,
                            filename=a.filename,
                            media_type=a.media_type,
                            created_at=a.created_at,
                        )
                        for a in j.attachments
                    ],
                )
                for j in db_doc.journal_entries
            ],
        )

    def get_by_id(self, document_id: int) -> Document | None:
        db_doc = self.db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        return self._to_domain(db_doc) if db_doc else None

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
        query = self.db.query(DocumentDB)

        # Joins for filtering
        if tag:
            query = query.join(DocumentDB.tags)
        if assignee or material_id or part_search:
            query = query.join(DocumentDB.tasks)
        if part_search:
            query = query.join(TaskDB.part_associations).join(PartDB)

        # Filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (DocumentDB.name.ilike(search_term)) | (DocumentDB.description.ilike(search_term))
            )

        if type:
            query = query.filter(DocumentDB.type == type)
        if status:
            query = query.filter(DocumentDB.status == status)

        if tag:
            query = query.filter(TagDB.name.ilike(f"%{tag}%"))

        if assignee:
            from .models import AssigneeDB

            # We already joined TaskDB above if assignee is present
            # query = query.join(DocumentDB.tasks) # Done in line 92
            # Now join assignees
            query = query.join(TaskDB.assignees).filter(AssigneeDB.name.ilike(f"%{assignee}%"))

        # Material filter (checking tasks)
        if material_id:
            query = query.filter(TaskDB.material_id == material_id)

        if part_search:
            query = query.filter(PartDB.name.ilike(f"%{part_search}%"))

        # Date Filtering
        if start_date or end_date:
            date_col = getattr(DocumentDB, date_field, DocumentDB.registration_date)
            if start_date:
                query = query.filter(date_col >= start_date)
            if end_date:
                query = query.filter(date_col <= end_date)

        # Sorting
        sort_col = getattr(DocumentDB, sort_by, DocumentDB.registration_date)
        if sort_order == "desc":
            query = query.order_by(desc(sort_col))
        else:
            query = query.order_by(sort_col)

        # Distinct needed if joining
        if tag or assignee or material_id or part_search:
            query = query.distinct()

        db_docs = query.offset(skip).limit(limit).all()
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
            done_date=document.done_date,
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

        # Update tags
        if document.tags is not None:
            # Clear existing relation
            db_doc.tags = []
            for tag in document.tags:
                # Find or create tag
                db_tag = self.db.query(TagDB).filter(TagDB.name == tag.name).first()
                if not db_tag:
                    db_tag = TagDB(name=tag.name)
                    self.db.add(db_tag)
                db_doc.tags.append(db_tag)

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
        doc_stats = (
            self.db.query(func.lower(DocumentDB.status), func.count(DocumentDB.id))
            .group_by(func.lower(DocumentDB.status))
            .all()
        )
        doc_by_status = {status: count for status, count in doc_stats}

        # Task Stats
        total_tasks = self.db.query(TaskDB).count()
        task_stats = (
            self.db.query(func.lower(TaskDB.status), func.count(TaskDB.id))
            .group_by(func.lower(TaskDB.status))
            .all()
        )
        task_by_status = {status: count for status, count in task_stats}

        assignee_stats = (
            self.db.query(AssigneeDB.name, func.count(TaskDB.id))
            .join(TaskDB.assignees)
            .group_by(AssigneeDB.name)
            .all()
        )
        task_by_assignee = {name: count for name, count in assignee_stats}

        # Inventory Stats
        total_parts = self.db.query(PartDB).count()
        total_materials = self.db.query(MaterialDB).count()
        stock_metrics = self.db.query(
            func.sum(StockItemDB.quantity).label("total_qty"),
            func.sum(StockItemDB.reserved).label("total_res"),
        ).first()

        # Journal Summary (Normalizing types)
        journal_stats = (
            self.db.query(func.lower(JournalEntryDB.type), func.count(JournalEntryDB.id))
            .group_by(func.lower(JournalEntryDB.type))
            .all()
        )
        journal_summary = {t: count for t, count in journal_stats}

        # Recent Activity (Last 10 Audit Logs)
        recent_logs = self.db.query(AuditLogDB).order_by(desc(AuditLogDB.timestamp)).limit(10).all()
        recent_activity = [
            {
                "actor": log.actor or "System",
                "action": log.action_type,
                "entity": log.entity_type,
                "entity_id": log.entity_id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in recent_logs
        ]

        return {
            "document_stats": {"total": total_docs, "by_status": doc_by_status},
            "task_stats": {
                "total": total_tasks,
                "by_status": task_by_status,
                "by_assignee": task_by_assignee,
            },
            "inventory": {
                "total_parts": total_parts,
                "total_materials": total_materials,
                "total_quantity": stock_metrics.total_qty or 0 if stock_metrics else 0,
                "total_reserved": stock_metrics.total_res or 0 if stock_metrics else 0,
            },
            "journal_summary": journal_summary,
            "recent_activity": recent_activity,
        }

    def delete_attachment(self, attachment_id: int) -> bool:
        db_att = self.db.query(AttachmentDB).filter(AttachmentDB.id == attachment_id).first()
        if db_att:
            self.db.delete(db_att)
            self.db.commit()
            return True
        return False

    def get_attachment(self, attachment_id: int) -> dict | None:
        db_att = self.db.query(AttachmentDB).filter(AttachmentDB.id == attachment_id).first()
        if db_att:
            return {
                "id": db_att.id,
                "document_id": db_att.document_id,
                "file_path": db_att.file_path,
                "filename": db_att.filename,
            }
        return None

    def create_order(self, name: str, items: builtins.list[dict]) -> Document:
        db_doc = DocumentDB(name=name, type=DocumentType.ORDER, status=DocumentStatus.IN_PROGRESS)
        self.db.add(db_doc)
        self.db.flush()

        for item in items:
            db_task = TaskDB(
                document_id=db_doc.id,
                name=f"Produce Part ID: {item['id']}",
                status=TaskStatus.PLANNED,
            )
            self.db.add(db_task)

        self.db.commit()
        self.db.refresh(db_doc)
        return self._to_domain(db_doc)

    def list_tags(self) -> builtins.list[Tag]:
        db_tags = self.db.query(TagDB).all()
        return [Tag(id=t.id, name=t.name) for t in db_tags]

    def save_as_new_order(self, data: dict) -> Document:
        # Create the Order Document
        db_doc = DocumentDB(
            name=data["name"],
            type=DocumentType.ORDER,
            status=DocumentStatus.IN_PROGRESS,
            content=json.dumps(data.get("project_data"))
            if data.get("project_data")
            else json.dumps({"original_document_id": data.get("original_document_id")}),
        )
        self.db.add(db_doc)
        self.db.flush()  # Get ID

        # Create Tasks (Sheets) and Attachments
        for sheet_item in data.get("sheets_processing", []):
            # Create Task for the sheet
            db_task = TaskDB(
                document_id=db_doc.id,
                name=sheet_item["name"],
                status=TaskStatus.PLANNED,
                gnc_file_path=sheet_item["file_path"],
            )
            self.db.add(db_task)

            # Create Attachment for the GNC file
            db_att = AttachmentDB(
                document_id=db_doc.id,
                filename=os.path.basename(sheet_item["file_path"]),
                file_path=sheet_item["file_path"],
                media_type="application/x-gnc",  # or text/plain
            )
            self.db.add(db_att)

        self.db.commit()
        self.db.refresh(db_doc)
        return self._to_domain(db_doc)


class SQLTaskRepository(ITaskRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, db_task: TaskDB) -> Task:
        from src.domain.models import Assignee

        return Task(
            id=db_task.id,
            document_id=db_task.document_id,
            material_id=db_task.material_id,
            name=db_task.name,
            status=db_task.status.lower() if db_task.status else TaskStatus.PLANNED,
            # assignee=db_task.assignee, # REMOVED
            assignees=[Assignee(id=a.id, name=a.name) for a in db_task.assignees],
            gnc_file_path=db_task.gnc_file_path,
            material=Material(id=db_task.material.id, name=db_task.material.name)
            if db_task.material
            else None,
            parts=[
                Part(id=p.id, name=p.name, registration_number=p.registration_number)
                for p in db_task.parts
            ],
        )

    def get_by_id(self, task_id: int) -> Task | None:
        db_task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        return self._to_domain(db_task) if db_task else None

    def list(self, skip: int = 0, limit: int = 100, filters: dict = None) -> list[Task]:
        query = self.db.query(TaskDB)
        if filters:
            if filters.get("assignee"):
                # Filter by assignee name via join
                from src.infrastructure.database.models import AssigneeDB

                query = query.join(TaskDB.assignees).filter(
                    AssigneeDB.name.ilike(f"%{filters['assignee']}%")
                )
            if filters.get("status"):
                query = query.filter(TaskDB.status == filters["status"])
        db_tasks = query.offset(skip).limit(limit).all()
        return [self._to_domain(t) for t in db_tasks]

    def add(self, task: Task) -> Task:
        from src.infrastructure.database.models import AssigneeDB

        db_task = TaskDB(
            document_id=task.document_id,
            material_id=task.material_id,
            name=task.name,
            status=(task.status or TaskStatus.PLANNED).lower(),
            # assignee=task.assignee, # REMOVED
            gnc_file_path=task.gnc_file_path,
        )

        # Add assignees
        if task.assignees:
            for asg in task.assignees:
                db_asg = self.db.query(AssigneeDB).filter(AssigneeDB.id == asg.id).first()
                if db_asg:
                    db_task.assignees.append(db_asg)

        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return self._to_domain(db_task)

    def update(self, task: Task) -> Task:
        from src.infrastructure.database.models import AssigneeDB

        db_task = self.db.query(TaskDB).filter(TaskDB.id == task.id).first()
        if not db_task:
            raise ValueError(f"Task with id {task.id} not found")

        db_task.name = task.name
        db_task.status = task.status.lower() if task.status else db_task.status
        # db_task.assignee = task.assignee # REMOVED
        db_task.gnc_file_path = task.gnc_file_path
        db_task.material_id = task.material_id

        # Update assignees
        if task.assignees is not None:
            # Clear existing
            db_task.assignees = []
            for asg in task.assignees:
                db_asg = self.db.query(AssigneeDB).filter(AssigneeDB.id == asg.id).first()
                if db_asg:
                    db_task.assignees.append(db_asg)

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

    def get_tasks_by_document_id(self, document_id: int) -> builtins.list[Task]:
        db_tasks = self.db.query(TaskDB).filter(TaskDB.document_id == document_id).all()
        return [self._to_domain(t) for t in db_tasks]


class SQLFilterPresetRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, db_preset: FilterPresetDB) -> FilterPreset:
        return FilterPreset(id=db_preset.id, name=db_preset.name, config=db_preset.config)

    def list(self) -> list[FilterPreset]:
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
