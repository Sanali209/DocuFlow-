"""TaskGroupService — manages TaskGroup lifecycle, replaces BatchEngine."""

from sqlmodel import Session, select

from docuflow.domain.entities.production import MaterialType, TaskGroup, TaskItem, TaskItemStatus


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
