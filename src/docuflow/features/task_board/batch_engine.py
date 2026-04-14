"""
BatchEngine — автоматическая группировка TaskItem по параметрам материала.

Группирует задачи для оптимизации переналадки станка.
Результат — batch_group_id (UUID) на связанных TaskItem.
"""

import itertools
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import Session, select

from docuflow.domain.entities.production import (
    ProductionUnit,
    TaskItem,
)


@dataclass
class BatchRule:
    """Правила группировки задач в батчи."""

    group_by: list[str] = field(
        default_factory=lambda: [
            "mat_type_id",
            "thickness",
            "sheet_x",
            "sheet_y",
        ]
    )
    include_other_work_items: bool = True
    max_batch_size: int | None = None


@dataclass
class BatchGroup:
    """Группа задач, объединённых в батч."""

    batch_group_id: UUID
    tasks: list[TaskItem]
    mat_type_id: int | None
    total_sheets: int
    estimated_minutes: int


@dataclass
class StockAlert:
    """Предупреждение о наличии детали в запасе."""

    sku: str
    units: list[ProductionUnit]


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

    def __init__(self, session: Session):
        self.session = session

    def compute(self, tasks: list[TaskItem], rule: BatchRule | None = None) -> list[BatchGroup]:
        """
        Группирует задачи по критериям материала.

        Args:
            tasks: Список задач для группировки
            rule: Правила группировки (необязательно, используются стандартные)

        Returns:
            List[BatchGroup] — список батчей
        """
        if rule is None:
            rule = BatchRule()

        if not tasks:
            return []

        def key_fn(t: TaskItem) -> tuple[Any, ...]:
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
                task_list = task_list[: rule.max_batch_size]

            batch_id = uuid4()
            groups.append(
                BatchGroup(
                    batch_group_id=batch_id,
                    tasks=task_list,
                    mat_type_id=task_list[0].mat_type_id if task_list else None,
                    total_sheets=sum(t.sheet_qty or 0 for t in task_list),
                    estimated_minutes=sum(t.estimated_minutes or 0 for t in task_list),
                )
            )

        return groups

    def apply_batches(self, groups: list[BatchGroup], session: Session | None = None) -> None:
        """
        Применяет батчи к базе данных.

        Args:
            groups: Список батчей
            session: SQLModel сессия (необязательно)
        """
        session = session or self.session
        for group in groups:
            for task in group.tasks:
                task.batch_group_id = str(group.batch_group_id)
                session.add(task)

        session.commit()

    def check_stock_alerts(
        self, tasks: list[TaskItem], session: Session | None = None
    ) -> list[StockAlert]:
        """
        Проверяет наличие деталей в запасе.

        Args:
            tasks: Список задач
            session: SQLModel сессия (необязательно)

        Returns:
            List[StockAlert] — список предупреждений
        """
        session = session or self.session
        alerts = []

        for task in tasks:
            for part in task.parts:
                # Ищем ProductionUnit с is_stock=True, содержащие эту деталь
                in_stock = session.exec(
                    select(ProductionUnit).where(ProductionUnit.is_stock == True)
                ).all()

                # Фильтруем по part_sku
                matching_units = [
                    u
                    for u in in_stock
                    if any(
                        tp.part_sku == part.part_sku
                        for tp in (u.task_item.parts if u.task_item else [])
                    )
                ]

                if matching_units:
                    alerts.append(StockAlert(sku=part.part_sku, units=matching_units))

        return alerts

    def move_task(
        self, task_id: int, new_batch_group_id: str, session: Session | None = None
    ) -> TaskItem:
        """
        Перемещает задачу в другой батч.

        Args:
            task_id: ID задачи
            new_batch_group_id: ID нового батча
            session: SQLModel сессия (необязательно)

        Returns:
            TaskItem — обновлённая задача

        Raises:
            ValueError: если задача не найдена
        """
        session = session or self.session
        task = session.get(TaskItem, task_id)
        if task is None:
            raise ValueError(f"Задача с ID {task_id} не найдена")

        task.batch_group_id = new_batch_group_id
        session.add(task)
        session.commit()
        session.refresh(task)

        return task

    def create_batch(self, task_ids: list[int], session: Session | None = None) -> str:
        """
        Создаёт новый батч для списка задач с валидацией материала.
        """
        session = session or self.session

        # Validation: Check if all tasks have the same material and thickness
        loaded_tasks: list[TaskItem] = []
        for tid in task_ids:
            task = session.get(TaskItem, tid)
            if task is None:
                raise ValueError(f"Задача с ID {tid} не найдена")
            loaded_tasks.append(task)

        if not loaded_tasks:
            raise ValueError("Список задач пуст")

        mat_ids = {t.mat_type_id for t in loaded_tasks}
        if len(mat_ids) > 1:
            raise ValueError("Нельзя объединять в один батч задачи с разными материалами")

        thicknesses = {t.thickness for t in loaded_tasks}
        if len(thicknesses) > 1:
            raise ValueError("Нельзя объединять в один батч задачи с разной толщиной")

        new_batch_id = str(uuid4())
        for task in loaded_tasks:
            task.batch_group_id = new_batch_id
            session.add(task)

        session.commit()
        return new_batch_id

    def split_batch(
        self,
        batch_group_id: str,
        task_ids_to_separate: list[int],
        session: Session | None = None,
    ) -> str:
        """
        Разделяет батч на два.

        Args:
            batch_group_id: ID исходного батча
            task_ids_to_separate: ID задач для разделения
            session: SQLModel сессия (необязательно)

        Returns:
            str — ID нового батча
        """
        session = session or self.session
        new_batch_id = str(uuid4())

        for task_id in task_ids_to_separate:
            task = session.get(TaskItem, task_id)
            if task and task.batch_group_id == batch_group_id:
                task.batch_group_id = new_batch_id
                session.add(task)

        session.commit()
        return new_batch_id
