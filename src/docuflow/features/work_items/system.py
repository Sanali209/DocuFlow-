import datetime
from enum import Enum
from typing import Optional, List, Any
from pathlib import Path
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.infrastructure.config import Config
from docuflow.domain.entities.production import (
    WorkItem,
    WorkItemStatus,
    WorkItemType,
    WorkLog,
    WorkLogType,
)

class WorkItemFilters(BaseModel):
    """Filter criteria for the WorkItem repository."""
    status: Optional[list[WorkItemStatus]] = None
    type: Optional[list[WorkItemType]] = None
    project_id: Optional[int] = None
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None
    search_text: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class WorkItemSystem(BaseSystem):
    """
    Core engine for managing the lifecycle of production orders (WorkItems).
    
    Principles:
    - Directed Status Transitions: Strictly enforces valid production state changes.
    - Full Traceability: Every status change and document registration is audit-logged.
    - Code as Documentation: Methods are self-describing and include usage examples.
    """
    
    # Validation rules for production state transitions
    VALID_TRANSITIONS: dict[WorkItemStatus, list[WorkItemStatus]] = {
        WorkItemStatus.NEW: [WorkItemStatus.REGISTERED, WorkItemStatus.IN_PROGRESS, WorkItemStatus.CANCELLED],
        WorkItemStatus.PENDING_CUTS: [WorkItemStatus.REGISTERED, WorkItemStatus.BLOCKED, WorkItemStatus.CANCELLED],
        WorkItemStatus.REGISTERED: [WorkItemStatus.IN_PROGRESS, WorkItemStatus.CANCELLED],
        WorkItemStatus.IN_PROGRESS: [WorkItemStatus.ON_HOLD, WorkItemStatus.DONE, WorkItemStatus.BLOCKED, WorkItemStatus.CANCELLED],
        WorkItemStatus.ON_HOLD: [WorkItemStatus.IN_PROGRESS, WorkItemStatus.CANCELLED],
        WorkItemStatus.BLOCKED: [WorkItemStatus.IN_PROGRESS, WorkItemStatus.CANCELLED],
        WorkItemStatus.DONE: [WorkItemStatus.ARCHIVED],
    }
    
    def __init__(self, config: Config, db_session: Session, sdk: Any = None):
        super().__init__(config)
        self.db_session = db_session
        self.sdk = sdk
    
    async def on_startup(self) -> None:
        """Lifecycle hook: System initialization."""
        pass
    
    async def on_shutdown(self) -> None:
        """Lifecycle hook: Resource cleanup."""
        pass
    
    # --- CRUD Operations ---

    def create_work_item(self, 
                         folder_name: str, 
                         item_type: WorkItemType, 
                         project_id: Optional[int] = None, 
                         **metadata) -> WorkItem:
        """
        Registers a new production order into the workshop tracking system.
        
        Example:
            new_item = system.create_work_item(
                folder_name="S-105-X", 
                item_type=WorkItemType.SIDRA
            )
        """
        # Default project fallback: Per architecture, everything starts in 'Default' (ID 1)
        target_project_id = project_id if project_id else 1
        
        work_item = WorkItem(
            folder_name=folder_name,
            work_item_type=item_type.value,
            project_id=target_project_id,
            status=WorkItemStatus.NEW.value,
            **metadata
        )
        
        db = self.db_session
        db.add(work_item)
        db.flush()
        db.refresh(work_item)
        
        # Log the initiation of the work item
        self._audit_status_change(work_item, f"WorkItem initialized: {folder_name}")
        
        return work_item
    
    def retrieve_work_item(self, work_item_id: int) -> WorkItem:
        """
        Locates a single production order by its database ID.
        """
        record = self.db_session.get(WorkItem, work_item_id)
        if record is None:
            raise ValueError(f"WorkItem ID {work_item_id} not found in the local registry.")
        return record
    
    def list_work_items_by_filter(self, criteria: WorkItemFilters) -> List[WorkItem]:
        """
        Retrieves a collection of orders matching specific workshop filters.
        
        Example:
            active_list = system.list_work_items_by_filter(
                WorkItemFilters(status=[WorkItemStatus.IN_PROGRESS])
            )
        """
        statement = select(WorkItem)
        
        if criteria.status:
            statement = statement.where(WorkItem.status.in_([s.value for s in criteria.status]))
        
        if criteria.type:
            statement = statement.where(WorkItem.work_item_type.in_([t.value for t in criteria.type]))
        
        if criteria.project_id is not None:
            statement = statement.where(WorkItem.project_id == criteria.project_id)
        
        if criteria.date_from:
            statement = statement.where(WorkItem.created_at >= criteria.date_from)
            
        if criteria.search_text:
            search_pattern = f"%{criteria.search_text}%"
            statement = statement.where(
                WorkItem.folder_name.ilike(search_pattern) |
                WorkItem.sidra_number.ilike(search_pattern)
            )
        
        # Execution with pagination
        statement = statement.offset(criteria.offset).limit(criteria.limit)
        return list(self.db_session.exec(statement).all())
    
    def update_work_item_metadata(self, work_item_id: int, **updates) -> WorkItem:
        """
        Updates descriptive fields of an existing production order.
        """
        work_item = self.retrieve_work_item(work_item_id)
        
        for field, value in updates.items():
            if hasattr(work_item, field):
                setattr(work_item, field, value)
        
        work_item.updated_at = datetime.datetime.now()
        self.db_session.add(work_item)
        self.db_session.flush()
        self.db_session.refresh(work_item)
        return work_item
    
    # --- Production Lifecycle Logic ---

    def register_physical_document(self, work_item_id: int, author: str) -> WorkItem:
        """
        Notes the arrival of physical paperwork at the workshop station.
        
        Example:
            system.register_physical_document(work_item_id=5, author="John Doe")
        """
        work_item = self.retrieve_work_item(work_item_id)
        work_item.doc_received_at = datetime.datetime.now()
        
        # Automatic state progression upon paper arrival
        if work_item.status in (WorkItemStatus.NEW.value, WorkItemStatus.PENDING_CUTS.value):
            work_item.status = WorkItemStatus.REGISTERED.value
        
        self._audit_status_change(work_item, f"Physical document registered by {author}")
        
        self.db_session.add(work_item)
        self.db_session.flush()
        return work_item
    
    def update_production_status(self, 
                                 work_item_id: int, 
                                 new_status: WorkItemStatus, 
                                 reason_note: Optional[str] = None) -> WorkItem:
        """
        Moves the production order to a new stage of the workshop pipeline.
        Enforces VALID_TRANSITIONS rules.
        
        Example:
            items.update_production_status(id=1, new_status=WorkItemStatus.IN_PROGRESS)
        """
        work_item = self.retrieve_work_item(work_item_id)
        current_status = WorkItemStatus(work_item.status)
        
        # Validation of transition integrity
        allowed_destinations = self.VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_destinations:
            raise ValueError(f"Illegal transition: {current_status.value} -> {new_status.value}. Check workflow rules.")
        
        work_item.status = new_status.value
        
        log_message = f"Status progression: {current_status.value} -> {new_status.value}"
        if reason_note:
            log_message += f" | Reason: {reason_note}"
        
        self._audit_status_change(work_item, log_message)
        
        self.db_session.add(work_item)
        self.db_session.flush()
        self.db_session.refresh(work_item)
        return work_item

    # --- Internal Helpers ---
    
    def _audit_status_change(self, work_item: WorkItem, message: str) -> None:
        """
        Internal helper to create persistent audit entries for status changes.
        """
        audit_entry = WorkLog(
            work_item_id=work_item.id,
            log_type=WorkLogType.STATUS_CHANGE.value,
            message=message,
            created_at=datetime.datetime.now(),
            node_id=self.config.node_id
        )
        self.db_session.add(audit_entry)