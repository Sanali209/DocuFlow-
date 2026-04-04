"""
BatchEngine — автоматическая группировка TaskItem по параметрам материала.

Группирует задачи для оптимизации переналадки станка.
Результат — batch_group_id (UUID) на связанных TaskItem.
"""
import itertools
from dataclasses import dataclass, field
from uuid import uuid4, UUID
from typing import Optional, List
from sqlmodel import Session, select

from docuflow.domain.entities.production import (
    TaskItem,
    TaskPart,
    ProductionUnit,
    WorkLog,
    WorkLogType,
)


@dataclass
class BatchRule:
    """Правила группировки задач в батчи."""
    group_by: list[str] = field(default_factory=lambda: [
        "mat_type_id",
        "thickness",
        "sheet_x",
        "sheet_y",
    ])
    include_other_work_items: bool = True
    max_batch_size: Optional[int] = None


@dataclass
class BatchGroup:
    """Группа задач, объединённых в батч."""
    batch_group_id: UUID
    tasks: List[TaskItem]
    mat_type_id: Optional[int]
    total_sheets: int
    estimated_minutes: int


@dataclass
class StockAlert:
    """Предупреждение о наличии детали в запасе."""
    sku: str
    units: List[ProductionUnit]


class BatchEngine:
    """
    Движок автоматической группировки задач в батчи.
    
    Основные операции:
    - compute — группировка задач по правилу
    - apply_batches — применение батчей к БД
    - check_stock_alerts — проверка наличия деталей в запасе
    - move_task — перемещение задачи между батчами
    - create_batch — создание нового батча
    - split_batch — разделение батча
    """
    
    def compute(self, tasks: List[TaskItem], rule: BatchRule) -> List[BatchGroup]:
        """
        Группирует задачи по критериям материала.
        
        Args:
            tasks: Список задач для группировки
            rule: Правила группировки
        
        Returns:
            List[BatchGroup] — список батчей
        """
        if not tasks:
            return []
        
        def key_fn(t: TaskItem) -> tuple:
            return tuple(getattr(t, field, None) for field in rule.group_by)
        
        # Сортировка по ключу группировки
        sorted_tasks = sorted(tasks, key=key_fn)
        
        groups = []
        for key, task_group in itertools.groupby(sorted_tasks, key=key_fn):
            task_list = list(task_group)
            
            # Сортировка внутри батча: step_index → batch_index
            task_list.sort(key=lambda t: (t.step_index or 0, t.batch_index or 0))
            
            # Ограничение размера батча
            if rule.max_batch_size and len(task_list) > rule.max_batch_size:
                task_list = task_list[:rule.max_batch_size]
            
            batch_id = uuid4()
            groups.append(BatchGroup(
                batch_group_id=batch_id,
                tasks=task_list,
                mat_type_id=task_list[0].mat_type_id if task_list else None,
                total_sheets=sum(t.sheet_qty or 0 for t in task_list),
                estimated_minutes=sum(t.estimated_minutes or 0 for t in task_list),
            ))
        
        return groups
    
    def apply_batches(self, groups: List[BatchGroup], session: Session) -> None:
        """
        Применяет батчи к базе данных.
        
        Args:
            groups: Список батчей
            session: SQLModel сессия
        """
        for group in groups:
            for task in group.tasks:
                task.batch_group_id = str(group.batch_group_id)
                session.add(task)
        
        session.commit()
    
    def check_stock_alerts(self, tasks: List[TaskItem], session: Session) -> List[StockAlert]:
        """
        Проверяет наличие деталей в запасе.
        
        Args:
            tasks: Список задач
            session: SQLModel сессия
        
        Returns:
            List[StockAlert] — список предупреждений
        """
        alerts = []
        
        for task in tasks:
            for part in task.parts:
                # Ищем ProductionUnit с is_stock=True, содержащие эту деталь
                in_stock = session.exec(
                    select(ProductionUnit)
                    .where(ProductionUnit.is_stock == True)
                ).all()
                
                # Фильтруем по part_sku
                matching_units = [
                    u for u in in_stock
                    if any(
                        tp.part_sku == part.part_sku
                        for tp in (u.task_item.parts if u.task_item else [])
                    )
                ]
                
                if matching_units:
                    alerts.append(StockAlert(
                        sku=part.part_sku,
                        units=matching_units
                    ))
        
        return alerts
    
    def move_task(self, task_id: int, new_batch_group_id: str, session: Session) -> TaskItem:
        """
        Перемещает задачу в другой батч.
        
        Args:
            task_id: ID задачи
            new_batch_group_id: ID нового батча
            session: SQLModel сессия
        
        Returns:
            TaskItem — обновлённая задача
        
        Raises:
            ValueError: если задача не найдена
        """
        task = session.get(TaskItem, task_id)
        if task is None:
            raise ValueError(f"Задача с ID {task_id} не найдена")
        
        task.batch_group_id = new_batch_group_id
        session.add(task)
        session.commit()
        session.refresh(task)
        
        return task
    
    def create_batch(self, task_ids: List[int], session: Session) -> str:
        """
        Создаёт новый батч для списка задач.
        
        Args:
            task_ids: Список ID задач
            session: SQLModel сессия
        
        Returns:
            str — ID нового батча
        """
        new_batch_id = str(uuid4())
        
        for task_id in task_ids:
            task = session.get(TaskItem, task_id)
            if task:
                task.batch_group_id = new_batch_id
                session.add(task)
        
        session.commit()
        return new_batch_id
    
    def split_batch(
        self,
        batch_group_id: str,
        task_ids_to_separate: List[int],
        session: Session,
    ) -> str:
        """
        Разделяет батч на два.
        
        Args:
            batch_group_id: ID исходного батча
            task_ids_to_separate: ID задач для разделения
            session: SQLModel сессия
        
        Returns:
            str — ID нового батча
        """
        new_batch_id = str(uuid4())
        
        for task_id in task_ids_to_separate:
            task = session.get(TaskItem, task_id)
            if task and task.batch_group_id == batch_group_id:
                task.batch_group_id = new_batch_id
                session.add(task)
        
        session.commit()
        return new_batch_id