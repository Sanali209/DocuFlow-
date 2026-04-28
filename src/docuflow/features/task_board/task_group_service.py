"""TaskGroupService — manages TaskGroup lifecycle, replaces BatchEngine."""

from dataclasses import dataclass

from sqlmodel import Session, select

from docuflow.domain.entities.production import (
    MaterialType,
    ProductionUnit,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
)


@dataclass
class StockAlert:
    """Предупреждение о наличии детали в запасе."""

    sku: str
    units: list[ProductionUnit]


class TaskGroupService:
    """Manages TaskGroup lifecycle — replaces BatchEngine."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def auto_group_by_material(self, work_item_id: int) -> list[TaskGroup]:
        """Group tasks by material+thickness."""
        tasks = list(
            self.session.exec(select(TaskItem).where(TaskItem.work_item_id == work_item_id)).all()
        )

        # Group by (mat_type_id, thickness)
        groups: dict[tuple[int | None, float | None], list[TaskItem]] = {}
        for task in tasks:
            key = (task.mat_type_id, task.thickness)
            groups.setdefault(key, []).append(task)

        result = []
        for (mat_id, thickness), task_list in groups.items():
            name = self._generate_group_name(mat_id, thickness)
            tg = TaskGroup(
                name=name,
                work_item_id=work_item_id,
                grouping_rule="auto_material",
            )
            self.session.add(tg)
            self.session.flush()

            for task in task_list:
                task.task_group_id = tg.id
                self.session.add(task)

            result.append(tg)

        self.session.commit()
        return result

    def _generate_group_name(self, mat_type_id: int | None, thickness: float | None) -> str:
        if mat_type_id:
            mat = self.session.get(MaterialType, mat_type_id)
            if mat:
                return f"{mat.code} {thickness or '-'}mm"
        return f"Unknown {thickness or '-'}mm"

    def create_manual_group(self, task_ids: list[int], name: str | None = None) -> TaskGroup:
        """Create manual group from task IDs."""
        tasks = []
        for tid in task_ids:
            task = self.session.get(TaskItem, tid)
            if task:
                tasks.append(task)

        if not tasks:
            raise ValueError("No tasks found")

        tg = TaskGroup(
            name=name or f"Group ({len(tasks)} tasks)",
            work_item_id=tasks[0].work_item_id,
            grouping_rule="manual",
        )
        self.session.add(tg)
        self.session.flush()

        for task in tasks:
            task.task_group_id = tg.id
            self.session.add(task)

        self.session.commit()
        return tg

    def get_group_status(self, group: TaskGroup) -> str:
        """Aggregate status from tasks."""
        statuses = {t.status for t in group.tasks}
        if TaskItemStatus.IN_PROGRESS in statuses:
            return "in_progress"
        if statuses == {TaskItemStatus.DONE}:
            return "done"
        if statuses == {TaskItemStatus.PLANNED}:
            return "planned"
        return "mixed"

    def move_task_to_group(self, task_id: int, group_id: int) -> None:
        task = self.session.get(TaskItem, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        group = self.session.get(TaskGroup, group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")
        task.task_group_id = group_id
        self.session.add(task)
        self.session.commit()

    def split_group(self, group_id: int, task_ids_to_separate: list[int]) -> TaskGroup:
        original = self.session.get(TaskGroup, group_id)
        if not original:
            raise ValueError(f"Group {group_id} not found")

        new_group = TaskGroup(
            name=f"{original.name} (split)",
            work_item_id=original.work_item_id,
            grouping_rule="manual",
        )
        self.session.add(new_group)
        self.session.flush()

        for tid in task_ids_to_separate:
            task = self.session.get(TaskItem, tid)
            if task and task.task_group_id == group_id:
                task.task_group_id = new_group.id
                self.session.add(task)

        self.session.commit()
        return new_group

    def merge_groups(self, group_ids: list[int]) -> TaskGroup:
        groups = []
        for gid in group_ids:
            g = self.session.get(TaskGroup, gid)
            if g:
                groups.append(g)

        if len(groups) < 2:
            raise ValueError("Need at least 2 groups to merge")

        merged = TaskGroup(
            name=f"Merged ({len(groups)} groups)",
            work_item_id=groups[0].work_item_id,
            grouping_rule="manual",
        )
        self.session.add(merged)
        self.session.flush()

        for g in groups:
            for task in g.tasks:
                task.task_group_id = merged.id
                self.session.add(task)

        self.session.commit()
        return merged

    def check_stock_alerts(self, tasks: list[TaskItem]) -> list[StockAlert]:
        """Проверяет наличие деталей в запасе."""
        alerts: list[StockAlert] = []

        from sqlalchemy.orm import selectinload

        in_stock = self.session.exec(
            select(ProductionUnit)
            .where(ProductionUnit.is_stock.is_(True))
            .options(selectinload(ProductionUnit.task_item).selectinload(TaskItem.parts))
        ).all()

        stock_map: dict[str, list[ProductionUnit]] = {}

        for u in in_stock:
            if u.task_item:
                for tp in u.task_item.parts:
                    stock_map.setdefault(tp.part_sku, []).append(u)

        for task in tasks:
            for part in task.parts:
                matching_units = stock_map.get(part.part_sku, [])

                if matching_units:
                    alerts.append(StockAlert(sku=part.part_sku, units=matching_units))

        return alerts
