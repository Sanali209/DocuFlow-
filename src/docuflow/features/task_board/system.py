"""
TaskBoardSystem — операционное сердце для оператора.

Управляет WorkerBucket, статусами TaskItem, трекингом прогресса,
передачей смены.
"""
import json
import datetime
from typing import Optional, List, Any
from uuid import UUID
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.infrastructure.config import Config

from docuflow.domain.entities.production import (
    TaskItem,
    TaskItemStatus,
    WorkItem,
    WorkItemStatus,
    WorkLog,
    WorkLogType,
    WorkerBucketEntry,
    ChatMessage,
    ChatMessageType,
)


# Правила допустимых переходов статусов TaskItem
ALLOWED_TRANSITIONS: dict[TaskItemStatus, list[TaskItemStatus]] = {
    TaskItemStatus.PLANNED: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
    TaskItemStatus.IN_PROGRESS: [
        TaskItemStatus.ON_HOLD,
        TaskItemStatus.DONE,
        TaskItemStatus.BLOCKED,
        TaskItemStatus.CANCELLED,
    ],
    TaskItemStatus.ON_HOLD: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
    TaskItemStatus.BLOCKED: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
}


from docuflow.features.inventory.system import InventorySystem
from docuflow.features.production.system import ProductionSystem


class TaskBoardSystem(BaseSystem):
    """
    Система управления задачами операторов.
    
    Vertical Slice: features/task_board/system.py
    
    Основные операции:
    - WorkerBucket: lock_batch, unlock_batch, get_bucket, handover
    - TaskItem lifecycle: start_task, pause_task, resume_task, block_task, complete_task
    - Трекинг: increment_sheets, get_drift
    """
    
    def __init__(self, 
                 config: Config, 
                 db_session: Session, 
                 ns_mirror=None, 
                 inventory_system: InventorySystem = None, 
                 production_system: ProductionSystem = None,
                 sdk: Any = None):
        """
        Initialize the TaskBoard management engine.
        
        Args:
            config: System configuration.
            db_session: SQLModel session for database persistence.
            ns_mirror: Optional service for Nesting Software integration.
            inventory_system: Optional engine for material write-offs.
            production_system: Optional engine for pallet/unit registration.
            sdk: Optional facade for cross-system requests.
        """
        super().__init__(config)
        self.db_session = db_session
        self.ns_mirror = ns_mirror
        self.inventory_system = inventory_system
        self.production_system = production_system
        self.sdk = sdk
    
    async def lock_batch(
        self,
        batch_group_id: str,
        node_id: str,
        operator: str,
    ) -> List[WorkerBucketEntry]:
        """
        Assigns a production batch to a specific operator on a workshop node.
        
        Example:
            entries = await system.lock_batch(
                batch_group_id="BATCH-001", 
                node_id="NODE-1", 
                operator="operator_name"
            )
        """
        task_items = self._get_batch_tasks(batch_group_id)
        bucket_entries = []
        
        for task_item in task_items:
            bucket_entry = WorkerBucketEntry(
                node_id=node_id,
                assigned_user=operator,
                task_item_id=task_item.id,
                batch_group_id=batch_group_id,
                locked_at=datetime.datetime.now(),
            )
            self.db_session.add(bucket_entry)
            
            task_item.assigned_to_node = node_id
            task_item.status = TaskItemStatus.PLANNED
            self.db_session.add(task_item)
            
            bucket_entries.append(bucket_entry)
        
        self.db_session.commit()
        
        # Notify integration services
        if self.ns_mirror:
            for bucket_entry in bucket_entries:
                await self.ns_mirror.on_bucket_add(bucket_entry)
        
        return bucket_entries
    
    async def unlock_batch(self, batch_group_id: str, node_id: str) -> None:
        """
        Releases a production batch from a workshop node, returning tasks to the global pool.
        """
        bucket_entries = self.db_session.exec(
            select(WorkerBucketEntry).where(
                WorkerBucketEntry.batch_group_id == batch_group_id,
                WorkerBucketEntry.node_id == node_id,
            )
        ).all()
        
        for bucket_entry in bucket_entries:
            task_item = self.db_session.get(TaskItem, bucket_entry.task_item_id)
            if task_item and task_item.status == TaskItemStatus.PLANNED:
                task_item.status = TaskItemStatus.NEW
                self.db_session.add(task_item)
            
            self.db_session.delete(bucket_entry)
        
        self.db_session.commit()
        
        if self.ns_mirror:
            for bucket_entry in bucket_entries:
                await self.ns_mirror.on_bucket_remove(bucket_entry)
    
    def get_bucket(self, node_id: str) -> List[WorkerBucketEntry]:
        """
        Retrieves the list of batches currently assigned to a workshop node.
        """
        return list(self.db_session.exec(
            select(WorkerBucketEntry).where(WorkerBucketEntry.node_id == node_id)
        ).all())
    
    def handover(self, node_id: str, receiving_operator: str, note: str) -> None:
        """
        Transfers all batches from the current operator to a new one (Shift Handover).
        
        Example:
            system.handover(node_id="NODE-1", receiving_operator="night_shift_user", note="Completed laser cuts")
        """
        bucket_entries = self.get_bucket(node_id)
        
        for bucket_entry in bucket_entries:
            bucket_entry.handover_note = note
            bucket_entry.handover_from = bucket_entry.assigned_user
            bucket_entry.handover_at = datetime.datetime.now()
            bucket_entry.assigned_user = receiving_operator
            self.db_session.add(bucket_entry)
        
        # Create a broadcast handover message
        if bucket_entries:
            chat_message = ChatMessage(
                author=bucket_entries[0].assigned_user,
                node_id=node_id,
                message_type=ChatMessageType.HANDOVER,
                content=f"Shift handover to {receiving_operator}. {note}",
            )
            self.db_session.add(chat_message)
        
        self.db_session.commit()
    
    def start_task(self, task_id: int) -> TaskItem:
        """
        Moves a task into active production (IN_PROGRESS).
        """
        task_item = self._validate_transition(task_id, TaskItemStatus.IN_PROGRESS)
        
        task_item.status = TaskItemStatus.IN_PROGRESS
        task_item.started_at = datetime.datetime.now()
        
        self._audit_task_event(task_item, WorkLogType.STATUS_CHANGE, "Task started")
        
        self.db_session.add(task_item)
        self.db_session.commit()
        self.db_session.refresh(task_item)
        
        return task_item
    
    def pause_task(self, task_id: int, reason: str) -> TaskItem:
        """
        Suspends task execution (ON_HOLD).
        """
        task_item = self._validate_transition(task_id, TaskItemStatus.ON_HOLD)
        task_item.status = TaskItemStatus.ON_HOLD
        
        self._audit_task_event(task_item, WorkLogType.ON_HOLD, reason, payload={"reason": reason})
        
        self.db_session.add(task_item)
        self.db_session.commit()
        self.db_session.refresh(task_item)
        return task_item
    
    def resume_task(self, task_id: int) -> TaskItem:
        """
        Resumes a suspended task.
        """
        task_item = self._validate_transition(task_id, TaskItemStatus.IN_PROGRESS)
        task_item.status = TaskItemStatus.IN_PROGRESS
        
        self._audit_task_event(task_item, WorkLogType.STATUS_CHANGE, "Task resumed")
        
        self.db_session.add(task_item)
        self.db_session.commit()
        self.db_session.refresh(task_item)
        return task_item
    
    def block_task(self, task_id: int, reason: str) -> TaskItem:
        """
        Блокирует задачу.
        
        Args:
            task_id: ID задачи
            reason: Причина блокировки
        
        Returns:
            TaskItem — обновлённая задача
        """
        task = self._validate_transition(task_id, TaskItemStatus.BLOCKED)
        
        task.status = TaskItemStatus.BLOCKED
        task.block_reason = reason
        
        self._log(task, WorkLogType.BLOCKED, reason)
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        
        return task
    
    def complete_task(
        self,
        task_id: int,
        sheets_done: int,
        qty_produced: int,
        create_pallet: bool = False
    ) -> TaskItem:
        """
        Finalizes task production, calculates performance metrics, and triggers material write-offs.
        
        Example:
            completed_task = system.complete_task(
                task_id=10, 
                sheets_done=5, 
                qty_produced=50, 
                create_pallet=True
            )
        """
        task_item = self._validate_transition(task_id, TaskItemStatus.DONE)
        
        task_item.status = TaskItemStatus.DONE
        task_item.sheets_done = sheets_done
        task_item.qty_produced = qty_produced
        task_item.completed_at = datetime.datetime.now()
        
        # Calculate performance metrics
        if task_item.started_at:
            total_duration_sec = (task_item.completed_at - task_item.started_at).total_seconds()
            total_minutes = total_duration_sec / 60.0
            
            # Deduct pauses from timeline
            pause_logs = self.db_session.exec(
                select(WorkLog).where(
                    WorkLog.task_item_id == task_item.id,
                    WorkLog.log_type == WorkLogType.ON_HOLD,
                )
            ).all()
            
            pause_minutes = 0.0
            for log in pause_logs:
                try:
                    payload = json.loads(log.payload or "{}")
                    pause_minutes += float(payload.get("duration_min", 0.0))
                except (json.JSONDecodeError, TypeError):
                    pass
            
            task_item.actual_minutes = int(max(0, total_minutes - pause_minutes))
        
        self._audit_task_event(task_item, WorkLogType.STATUS_CHANGE, "Task completed")
        
        # Automated material write-off
        if self.inventory_system and task_item.mat_type_id and task_item.sheets_done:
            try:
                self.inventory_system.perform_write_off(
                    task_item_id=task_item.id,
                    mat_type_id=task_item.mat_type_id,
                    qty=float(task_item.sheets_done)
                )
            except Exception as e:
                logger.error(f"Failed to perform material write-off for task {task_item.id}: {e}")

        # Automated unit registration
        if create_pallet and self.production_system:
            try:
                self.production_system.register_finished_pallet(
                    task_item_id=task_item.id,
                    quantity=qty_produced or 1,
                    author_name="operator"
                )
            except Exception as e:
                logger.error(f"Failed to register production unit for task {task_item.id}: {e}")

        # Check grouping completion
        self._check_batch_completion(task_item.work_item_id)
        
        self.db_session.add(task_item)
        self.db_session.commit()
        self.db_session.refresh(task_item)
        
        return task_item
    
    def increment_sheets(self, task_id: int) -> int:
        """
        Increments the counter for processed sheets on a specific task.
        """
        task_item = self.db_session.get(TaskItem, task_id)
        if task_item is None:
            raise ValueError(f"Task {task_id} not found")
        
        task_item.sheets_done += 1
        self.db_session.add(task_item)
        self.db_session.commit()
        
        return task_item.sheets_done
    
    def get_drift(self, task_item: TaskItem) -> float:
        """
        Calculates the percentage deviation between estimated and actual production time.
        """
        if not task_item.estimated_minutes or not task_item.actual_minutes:
            return 0.0
        
        return (task_item.actual_minutes - task_item.estimated_minutes) / task_item.estimated_minutes * 100
    
    def _get_batch_tasks(self, batch_group_id: str) -> List[TaskItem]:
        """
        Retrieves all task items associated with a specific production batch.
        """
        return list(self.db_session.exec(
            select(TaskItem).where(TaskItem.batch_group_id == batch_group_id)
        ).all())
    
    def _validate_transition(self, task_id: int, new_status: TaskItemStatus) -> TaskItem:
        """
        Validates whether a production status change is allowed under current workflow rules.
        """
        task_item = self.db_session.get(TaskItem, task_id)
        if task_item is None:
            raise ValueError(f"Task ID {task_id} not found")
        
        current_status = TaskItemStatus(task_item.status)
        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition for Task {task_id}: {current_status.value} -> {new_status.value}. "
                f"Valid options: {[s.value for s in allowed]}"
            )
        
        return task_item
    
    def _check_batch_completion(self, work_item_id: int) -> None:
        """
        Audits if all tasks within a WorkItem (Order Batch) are completed, then promotes the WorkItem status.
        """
        work_item = self.db_session.get(WorkItem, work_item_id)
        if work_item is None:
            return
        
        # Aggregate all tasks for this order
        task_items = self.db_session.exec(
            select(TaskItem).where(TaskItem.work_item_id == work_item_id)
        ).all()
        
        # Transition to DONE only if all items reach terminal state
        if all(item.status == TaskItemStatus.DONE for item in task_items):
            work_item.status = WorkItemStatus.DONE.value
            work_item.completed_at = datetime.datetime.now()
            self.db_session.add(work_item)
    
    def _audit_task_event(
        self,
        task_item: TaskItem,
        log_type: WorkLogType,
        message: str,
        payload: Optional[dict] = None,
    ) -> None:
        """
        Creates a persistent audit trail for workshop operations in the WorkLog repository.
        """
        work_log = WorkLog(
            task_item_id=task_item.id,
            work_item_id=task_item.work_item_id,
            log_type=log_type.value,
            message=message,
            payload=json.dumps(payload) if payload else None,
            created_at=datetime.datetime.now(),
            node_id=self.config.node_id
        )
        self.db_session.add(work_log)