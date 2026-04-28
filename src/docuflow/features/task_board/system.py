"""
TaskBoardSystem — операционное сердце для оператора.

Управляет WorkerBucket, статусами TaskItem, трекингом прогресса,
передачей смены.
"""

import datetime
import json
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, ClassVar

from loguru import logger
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    ProductionUnit,
    Project,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
    WorkerBucketEntry,
    WorkItem,
    WorkItemStatus,
    WorkLog,
    WorkLogType,
)
from docuflow.features.inventory.system import InventorySystem
from docuflow.features.production.system import ProductionSystem
from docuflow.infrastructure.config import Config


class TaskBoardSystem(BaseSystem):
    """
    TaskBoardSystem — операционное сердце для оператора.
    Управляет жизненным циклом задач на конкретном узле.
    """

    SHEET_OVERAGE_TOLERANCE = 1.2

    VALID_TASK_TRANSITIONS: ClassVar[dict[TaskItemStatus, list[TaskItemStatus]]] = {
        TaskItemStatus.PLANNED: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
        TaskItemStatus.IN_PROGRESS: [
            TaskItemStatus.ON_HOLD,
            TaskItemStatus.SUSPENDED,
            TaskItemStatus.DONE,
            TaskItemStatus.BLOCKED,
            TaskItemStatus.CANCELLED,
        ],
        TaskItemStatus.ON_HOLD: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
        TaskItemStatus.SUSPENDED: [
            TaskItemStatus.IN_PROGRESS,
            TaskItemStatus.DONE,
            TaskItemStatus.CANCELLED,
        ],
        TaskItemStatus.BLOCKED: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
        TaskItemStatus.DONE: [],
        TaskItemStatus.CANCELLED: [],
    }

    def __init__(
        self,
        config: Config,
        db_engine: Any,
        session: Session | None = None,
        ns_mirror: Any = None,
        inventory_system: InventorySystem | None = None,
        production_system: ProductionSystem | None = None,
        sdk: Any = None,
    ):
        super().__init__(config, session)
        self.db_engine = db_engine
        self.ns_mirror = ns_mirror
        self.inventory_system = inventory_system
        self.production_system = production_system
        self.sdk = sdk

    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """
        Provides a session for database operations.

        Priority: 1) Injected session (from DI), 2) Create new session from engine.
        """
        if self.session is not None:
            yield self.session
        elif self.db_engine is not None:
            with Session(self.db_engine) as session:
                yield session
                session.commit()
        else:
            raise RuntimeError(f"{self.__class__.__name__}: No session or db_engine available")

    def _sync(self, session: Session):
        """Internal helper to flush or commit based on session ownership."""
        if self.session is not None:
            session.flush()
        else:
            session.commit()

    async def lock_batch(
        self,
        batch_group_id: str,
        node_id: str,
        operator: str,
    ) -> list[WorkerBucketEntry]:
        """
        Marks a group of tasks as 'PLANNED' and assigns them to a specific node/worker.
        """
        with self.get_db_session() as session:
            task_items = list(
                session.exec(
                    select(TaskItem).where(TaskItem.batch_group_id == batch_group_id)
                ).all()
            )
            bucket_entries = []

            for task_item in task_items:
                if task_item.id is None:
                    continue
                bucket_entry = WorkerBucketEntry(
                    node_id=node_id,
                    assigned_user=operator,
                    task_item_id=task_item.id,
                    batch_group_id=batch_group_id,
                    locked_at=datetime.datetime.now(),
                )
                session.add(bucket_entry)

                task_item.assigned_to_node = node_id
                task_item.status = TaskItemStatus.PLANNED
                session.add(task_item)
                bucket_entries.append(bucket_entry)

            # Audit trail
            log = WorkLog(
                log_type=WorkLogType.INFO,
                message=f"Batch {batch_group_id} locked by {operator} on {node_id}",
                node_id=self.config.node_id,
            )
            session.add(log)
            self._sync(session)

            # Note: NSMirrorService doesn't have on_bucket_add method
            # This integration point is reserved for future bucket→NS sync

            return bucket_entries

    def get_bucket(self, node_id: str) -> list[WorkerBucketEntry]:
        """Получает все записи корзины для указанного узла."""
        from loguru import logger

        logger.debug(f"get_bucket called: node_id={node_id!r}, type={type(node_id)}")

        with self.get_db_session() as session:
            return list(
                session.exec(
                    select(WorkerBucketEntry).where(WorkerBucketEntry.node_id == node_id)
                ).all()
            )

    def start_task(self, task_id: int) -> TaskItem:
        with self.get_db_session() as session:
            task_item = self._validate_transition(task_id, TaskItemStatus.IN_PROGRESS, session)
            task_item.status = TaskItemStatus.IN_PROGRESS
            task_item.started_at = datetime.datetime.now()
            self._audit_task_event(
                task_item, WorkLogType.STATUS_CHANGE, "Task started", session=session
            )
            session.add(task_item)
            self._sync(session)
            session.refresh(task_item)
            return task_item

    def pause_task(self, task_id: int, reason: str) -> TaskItem:
        with self.get_db_session() as session:
            task_item = self._validate_transition(task_id, TaskItemStatus.ON_HOLD, session)
            task_item.status = TaskItemStatus.ON_HOLD
            task_item.block_reason = reason
            self._audit_task_event(
                task_item, WorkLogType.ON_HOLD, f"Paused: {reason}", session=session
            )
            session.add(task_item)
            self._sync(session)
            session.refresh(task_item)
            return task_item

    def suspend_task(self, task_id: int) -> TaskItem:
        with self.get_db_session() as session:
            task_item = self._validate_transition(task_id, TaskItemStatus.SUSPENDED, session)
            task_item.status = TaskItemStatus.SUSPENDED
            self._audit_task_event(
                task_item, WorkLogType.STATUS_CHANGE, "Task suspended", session=session
            )
            session.add(task_item)
            self._sync(session)
            session.refresh(task_item)
            return task_item

    def resume_task(self, task_id: int) -> TaskItem:
        with self.get_db_session() as session:
            task_item = self._validate_transition(task_id, TaskItemStatus.IN_PROGRESS, session)
            task_item.status = TaskItemStatus.IN_PROGRESS
            self._audit_task_event(
                task_item, WorkLogType.STATUS_CHANGE, "Task resumed", session=session
            )
            session.add(task_item)
            self._sync(session)
            session.refresh(task_item)
            return task_item

    def complete_task(
        self, task_id: int, sheets_done: int, qty_produced: int = 0, create_pallet: bool = False
    ) -> TaskItem:
        with self.get_db_session() as session:
            task_item = self._validate_transition(task_id, TaskItemStatus.DONE, session)

            # Validation: Prevent accidental over-entry (e.g. 100 instead of 10)
            planned = task_item.sheet_qty or 0
            if sheets_done > (planned * self.SHEET_OVERAGE_TOLERANCE) and planned > 0:
                raise ValueError(
                    f"Количество листов ({sheets_done}) значительно превышает "
                    f"план ({planned}). Проверьте ввод."
                )

            if qty_produced < 0:
                raise ValueError("Количество произведенных деталей не может быть отрицательным.")

            # Auto-calculate qty_produced from TaskParts
            if task_item.parts:
                parts_per_sheet = sum(p.qty for p in task_item.parts)
                auto_qty = parts_per_sheet * sheets_done
            else:
                auto_qty = sheets_done

            # Use auto if qty_produced is 0 or not provided
            final_qty = auto_qty if qty_produced == 0 else qty_produced

            task_item.status = TaskItemStatus.DONE
            task_item.completed_at = datetime.datetime.now()
            task_item.sheets_done = sheets_done
            task_item.qty_produced = final_qty

            # Calculate actual time
            if task_item.started_at:
                delta = task_item.completed_at - task_item.started_at
                task_item.actual_minutes = int(delta.total_seconds() / 60)

            self._audit_task_event(
                task_item, WorkLogType.STATUS_CHANGE, "Task completed", session=session
            )

            # Material write-off
            if self.inventory_system:
                try:
                    self.inventory_system.perform_write_off(
                        task_item, sheets_used=sheets_done, author="operator"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to perform material write-off for task {task_item.id}: {e}"
                    )

            # Automated unit registration
            if create_pallet and self.production_system and task_item.id is not None:
                try:
                    self.production_system.register_finished_pallet(
                        task_item_id=task_item.id,  # type: ignore[arg-type]
                        quantity=task_item.qty_produced,
                        author_name="operator",
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to register production output for task {task_item.id}: {e}"
                    )

            session.add(task_item)
            self._sync(session)
            session.refresh(task_item)

            # Auto-close WorkItem if all tasks are finished
            self._check_and_auto_close_work_item(task_item.work_item_id, session)

            return task_item

    def _check_and_auto_close_work_item(self, work_item_id: int, session: Session) -> None:
        """Checks if all tasks for a work item are completed and closes it if so."""
        all_tasks = list(
            session.exec(select(TaskItem).where(TaskItem.work_item_id == work_item_id)).all()
        )

        if not all_tasks:
            return

        if all(t.status in [TaskItemStatus.DONE, TaskItemStatus.CANCELLED] for t in all_tasks):
            work_item = session.get(WorkItem, work_item_id)
            if work_item and work_item.status != WorkItemStatus.DONE:
                work_item.status = WorkItemStatus.DONE
                work_item.completed_at = datetime.datetime.now()
                session.add(work_item)

                # Audit the auto-close
                self._audit_task_event(
                    all_tasks[0],
                    WorkLogType.INFO,
                    "Наряд автоматически закрыт (все задачи завершены)",
                    session=session,
                )
                self._sync(session)
                logger.info(f"WorkItem {work_item_id} auto-closed.")

    def block_task(self, task_id: int, reason: str) -> TaskItem:
        with self.get_db_session() as session:
            task_item = self._validate_transition(task_id, TaskItemStatus.BLOCKED, session)
            task_item.status = TaskItemStatus.BLOCKED
            task_item.block_reason = reason
            self._audit_task_event(
                task_item, WorkLogType.BLOCKED, f"Blocked: {reason}", session=session
            )
            session.add(task_item)
            self._sync(session)
            session.refresh(task_item)
            return task_item

    def report_material_incident(self, task_id: int, reason: str) -> None:
        """Регистрирует инцидент по материалу и уведомляет чат."""
        with self.get_db_session() as session:
            task = session.get(TaskItem, task_id)
            if not task:
                return

            # 1. Запись в аудит наряда
            message = f"[MATERIAL_INCIDENT] {reason}"
            self._audit_task_event(
                task,
                WorkLogType.ON_HOLD,
                message,
                payload={"incident": True, "reason": reason},
                session=session,
            )

            # 2. Логгирование и фиксация
            self._sync(session)
            logger.warning(f"Material incident reported for task {task_id}: {reason}")

    async def assign_task_to_node(
        self,
        task_id: int,
        node_id: str,
        operator: str,
    ) -> WorkerBucketEntry:
        """Назначает одиночную задачу на конкретный узел."""
        with self.get_db_session() as session:
            task = session.get(TaskItem, task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            task_id_val = task.id
            if task_id_val is None:
                raise ValueError(f"Task {task_id} has no ID")

            # Создаем уникальный ID батча для этой задачи (сингл-батч)
            import uuid

            single_batch_id = str(uuid.uuid4())

            bucket_entry = WorkerBucketEntry(
                node_id=node_id,
                assigned_user=operator,
                task_item_id=task_id_val,  # type: ignore[arg-type]
                batch_group_id=single_batch_id,
                locked_at=datetime.datetime.now(),
            )
            session.add(bucket_entry)

            task.assigned_to_node = node_id
            task.batch_group_id = single_batch_id
            task.status = TaskItemStatus.PLANNED
            session.add(task)

            self._sync(session)

            if self.ns_mirror:
                await self.ns_mirror.on_bucket_add(bucket_entry)

            return bucket_entry

    def move_work_item_to_project(self, work_item_id: int, project_id: int) -> None:
        """Move a WorkItem to a different Project."""
        with self.get_db_session() as session:
            wi = session.get(WorkItem, work_item_id)
            if wi is None:
                raise ValueError(f"WorkItem {work_item_id} not found")
            project = session.get(Project, project_id)
            if project is None:
                raise ValueError(f"Project {project_id} not found")
            wi.project_id = project_id
            session.add(wi)
            self._sync(session)

    def assign_task_group_to_node(self, task_group_id: int, node_id: str) -> None:
        """Assign all tasks in a TaskGroup to a node."""
        with self.get_db_session() as session:
            tg = session.get(TaskGroup, task_group_id)
            if tg is None:
                raise ValueError(f"TaskGroup {task_group_id} not found")
            for task in tg.tasks:
                task.assigned_to_node = node_id
                session.add(task)
            self._sync(session)

            # Auto-create material reservation
            if self.inventory_system is not None:
                material_sheets: dict[int, int] = {}
                for task in tg.tasks:
                    if task.mat_type_id is not None:
                        material_sheets[task.mat_type_id] = material_sheets.get(
                            task.mat_type_id, 0
                        ) + (task.sheet_qty or 0)
                for mat_id, qty in material_sheets.items():
                    try:
                        self.inventory_system.create_reservation(
                            stock_item_id=mat_id,
                            work_item_id=tg.work_item_id,
                            qty=qty,
                            is_hard=False,
                        )
                    except Exception:
                        logger.warning("Reservation failed during task assignment — continuing")

    def get_matching_unassigned_tasks(self, mat_type_id: int, thickness: float) -> list[TaskItem]:
        """Ищет неназначенные задачи с таким же материалом и толщиной."""
        with self.get_db_session() as session:
            statement = select(TaskItem).where(
                TaskItem.assigned_to_node == None,  # noqa: E711  # type: ignore[attr-defined]
                TaskItem.mat_type_id == mat_type_id,
                TaskItem.thickness == thickness,
                TaskItem.status.in_([TaskItemStatus.PLANNED]),  # type: ignore[attr-defined]
            )
            return list(session.exec(statement).all())

    def handover(self, node_id: str, to_operator: str, note: str) -> None:
        """Передает смену новому оператору, оставляя заметку."""
        with self.get_db_session() as session:
            bucket_entries = session.exec(
                select(WorkerBucketEntry).where(WorkerBucketEntry.node_id == node_id)
            ).all()

            for entry in bucket_entries:
                entry.handover_from = entry.assigned_user
                entry.assigned_user = to_operator
                entry.handover_note = note
                entry.handover_at = datetime.datetime.now()
                session.add(entry)

            self._sync(session)
            logger.info(f"Handover on {node_id} to {to_operator}: {note}")

    def increment_sheets(self, task_id: int) -> int:
        """Увеличивает счетчик порезанных листов."""
        with self.get_db_session() as session:
            task = session.get(TaskItem, task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            task.sheets_done += 1
            session.add(task)
            self._sync(session)
            session.refresh(task)
            return task.sheets_done

    def get_drift(self, task: TaskItem) -> float:
        """Calculates percentage drift from estimated time."""
        if not task.estimated_minutes or not task.actual_minutes:
            return 0.0
        return (task.actual_minutes - task.estimated_minutes) / task.estimated_minutes * 100

    def get_node_drift(self, node_id: str) -> float:
        """Calculates the average Drift % for all completed tasks on a node."""
        with self.get_db_session() as session:
            bucket_entries = self.get_bucket(node_id)
            total_estimated = 0
            total_actual = 0
            for entry in bucket_entries:
                task = session.get(TaskItem, entry.task_item_id)
                if task and task.status == TaskItemStatus.DONE:
                    total_estimated += task.estimated_minutes or 0
                    total_actual += task.actual_minutes or 0

            if total_estimated == 0:
                return 0.0
            return (total_actual - total_estimated) / total_estimated * 100

    def get_node_status(self, node_id: str) -> str:
        """Returns a human-readable status for the node based on its current tasks."""
        with self.get_db_session() as session:
            bucket = self.get_bucket(node_id)
            if not bucket:
                return "Свободен"

            tasks = []
            for entry in bucket:
                task = session.get(TaskItem, entry.task_item_id)
                if task:
                    tasks.append(task)

            if any(t.status == TaskItemStatus.IN_PROGRESS for t in tasks):
                return "Режет"
            elif any(t.status == TaskItemStatus.ON_HOLD for t in tasks):
                return "На паузе"
            else:
                return "Ожидание"

    def get_unassigned_tasks(self, work_item_id: int | None = None) -> list[TaskItem]:
        """Retrieves tasks that haven't been assigned to any node."""
        with self.get_db_session() as session:
            statement = select(TaskItem).where(
                TaskItem.assigned_to_node == None,  # noqa: E711  # type: ignore[attr-defined]
                TaskItem.status == TaskItemStatus.PLANNED,
            )

            if work_item_id:
                statement = statement.where(TaskItem.work_item_id == work_item_id)

            return list(session.exec(statement).all())

    def find_pallets_by_task(
        self, task_id: int, session: Session | None = None
    ) -> list[ProductionUnit]:
        """Find all production units (pallets) linked to a specific task."""
        if session is not None:
            return list(
                session.exec(
                    select(ProductionUnit).where(ProductionUnit.task_item_id == task_id)
                ).all()
            )
        with self.get_db_session() as session:
            return list(
                session.exec(
                    select(ProductionUnit).where(ProductionUnit.task_item_id == task_id)
                ).all()
            )

    def find_pallets_by_work_item(
        self, work_item_id: int, session: Session | None = None
    ) -> list[ProductionUnit]:
        """Find all production units linked to tasks of a specific work item."""
        if session is not None:
            return list(
                session.exec(
                    select(ProductionUnit)
                    .join(TaskItem)
                    .where(TaskItem.work_item_id == work_item_id)
                ).all()
            )
        with self.get_db_session() as session:
            return list(
                session.exec(
                    select(ProductionUnit)
                    .join(TaskItem)
                    .where(TaskItem.work_item_id == work_item_id)
                ).all()
            )

    def find_pallets_by_project(
        self, project_id: int, session: Session | None = None
    ) -> list[ProductionUnit]:
        """Find all production units linked to tasks of a specific project."""
        if session is not None:
            return list(
                session.exec(
                    select(ProductionUnit)
                    .join(TaskItem)
                    .join(WorkItem)
                    .where(WorkItem.project_id == project_id)
                ).all()
            )
        with self.get_db_session() as session:
            return list(
                session.exec(
                    select(ProductionUnit)
                    .join(TaskItem)
                    .join(WorkItem)
                    .where(WorkItem.project_id == project_id)
                ).all()
            )

    def find_task_by_pallet_label(
        self, label_id: str, session: Session | None = None
    ) -> TaskItem | None:
        """Find the task associated with a pallet by its label ID."""
        if session is not None:
            pallet = session.exec(
                select(ProductionUnit).where(ProductionUnit.label_id == label_id)
            ).first()
            return pallet.task_item if pallet else None
        with self.get_db_session() as session:
            pallet = session.exec(
                select(ProductionUnit).where(ProductionUnit.label_id == label_id)
            ).first()
            return pallet.task_item if pallet else None

    def _validate_transition(
        self, task_id: int, target_status: TaskItemStatus, session: Session
    ) -> TaskItem:
        """Проверяет корректность перехода статуса (TDD)."""
        task = session.get(TaskItem, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        current = task.status
        allowed = self.VALID_TASK_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise ValueError(
                f"Invalid transition from {current.name} to {target_status.name}. "
                f"Allowed: {[s.name for s in allowed]}"
            )

        return task

    def _audit_task_event(
        self,
        task: TaskItem,
        log_type: WorkLogType,
        message: str,
        payload: dict | None = None,
        session: Session | None = None,
    ):
        """Создает запись в WorkLog."""
        target_session = session or self.db_session
        work_log = WorkLog(
            work_item_id=task.work_item_id,
            task_item_id=task.id,
            log_type=log_type,
            message=message,
            payload=json.dumps(payload) if payload else None,
            created_at=datetime.datetime.now(),
            node_id=self.config.node_id,
        )
        target_session.add(work_log)
        if not session and not self.session:
            target_session.commit()
