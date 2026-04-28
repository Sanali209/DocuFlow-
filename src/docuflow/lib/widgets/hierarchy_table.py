from functools import partial
from typing import Any

from nicegui import ui
from sqlmodel import Session, select

from docuflow.domain.entities.production import (
    Project,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
    WorkItem,
)
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.task_board.task_group_service import TaskGroupService
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.hierarchy_row import HierarchyRow

STATUS_COLORS = {
    "in_progress": "orange",
    "done": "green",
    "planned": "blue",
    "mixed": "yellow",
}

TASK_STATUS_COLORS = {
    TaskItemStatus.PLANNED: "blue",
    TaskItemStatus.IN_PROGRESS: "green",
    TaskItemStatus.ON_HOLD: "yellow",
    TaskItemStatus.SUSPENDED: "orange",
    TaskItemStatus.DONE: "gray",
    TaskItemStatus.BLOCKED: "red",
}


class HierarchyTable(BaseDocuWidget):
    """Tree-like hierarchy: Project → WorkItem → TaskGroup → TaskItem."""

    def __init__(
        self,
        user_id: str,
        view_name: str,
        system_scope: Any,
        filters: dict | None = None,
    ):
        super().__init__(system_scope)
        self.user_id = user_id
        self.view_name = view_name
        self.filters = filters or {}

    async def render(self) -> None:
        with ui.column().classes("w-full gap-2"):
            async with self.scope() as req:
                session = await req.get(Session)
                tb_system = await req.get(TaskBoardSystem)

                projects = list(session.exec(select(Project)).all())

                for project in projects:
                    self._render_project(session, tb_system, project)

    def _render_project(
        self, session: Session, tb_system: TaskBoardSystem, project: Project
    ) -> None:
        work_items = list(
            session.exec(select(WorkItem).where(WorkItem.project_id == project.id)).all()
        )

        def toggle(expanded: bool) -> None:
            pass

        row = HierarchyRow(
            icon="folder",
            title=project.name,
            badges=[(f"{len(work_items)} нарядов", "blue")],
            line2=project.description or "",
            is_expandable=True,
            is_expanded=True,
            on_toggle=toggle,
            system_scope=self.system_scope,
        )
        row.render()

        if row.is_expanded:
            for wi in work_items:
                self._render_workitem(session, tb_system, wi, indent=1)

    def _render_workitem(
        self, session: Session, tb_system: TaskBoardSystem, wi: WorkItem, indent: int
    ) -> None:
        task_groups = list(
            session.exec(select(TaskGroup).where(TaskGroup.work_item_id == wi.id)).all()
        )
        ungrouped = list(
            session.exec(
                select(TaskItem).where(
                    TaskItem.work_item_id == wi.id,
                    TaskItem.task_group_id.is_(None),  # type: ignore[attr-defined]
                )
            ).all()
        )

        total_tasks = sum(len(g.tasks) for g in task_groups) + len(ungrouped)

        row = HierarchyRow(
            icon="inventory_2",
            title=wi.folder_name,
            badges=[(wi.status.value, "gray"), (f"{total_tasks} задач", "teal")],
            line2=(
                f"SIDRA: {wi.sidra_number or '-'} | "
                f"Проект: {wi.project.name if wi.project else '-'}"
            ),
            is_expandable=True,
            is_expanded=False,
            actions=[("Редактировать", lambda: None)],
            indent=indent,
            system_scope=self.system_scope,
        )
        row.render()

        if row.is_expanded:
            for tg in task_groups:
                self._render_taskgroup(session, tb_system, tg, indent=indent + 1)
            for task in ungrouped:
                self._render_taskitem(session, tb_system, task, indent=indent + 1)

    def _render_taskgroup(
        self, session: Session, tb_system: TaskBoardSystem, tg: TaskGroup, indent: int
    ) -> None:
        tg_service = TaskGroupService(session)
        status = tg_service.get_group_status(tg)
        total_sheets = sum(t.sheet_qty or 0 for t in tg.tasks)
        done_sheets = sum(t.sheets_done or 0 for t in tg.tasks)

        status_color = STATUS_COLORS.get(status, "gray")

        line2 = f"Листов: {done_sheets}/{total_sheets}"
        done_tasks = [t for t in tg.tasks if t.status == TaskItemStatus.DONE and t.id is not None]
        if done_tasks:
            pallet_count = 0
            for t in done_tasks:
                if t.id is not None:
                    pallet_count += len(tb_system.find_pallets_by_task(t.id, session))
            if pallet_count > 0:
                line2 += f" | {pallet_count} паллет"

        row = HierarchyRow(
            icon="layers",
            title=tg.name or f"Группа {tg.id}",
            badges=[(f"{len(tg.tasks)} задач", status_color), (status, status_color)],
            line2=line2,
            is_expandable=True,
            is_expanded=False,
            indent=indent,
            system_scope=self.system_scope,
        )
        row.render()

        if row.is_expanded:
            for task in tg.tasks:
                self._render_taskitem(session, tb_system, task, indent=indent + 1)

    def _render_taskitem(
        self, session: Session, tb_system: TaskBoardSystem, task: TaskItem, indent: int
    ) -> None:
        progress_str = f"{task.sheets_done}/{task.sheet_qty} листов"

        status_color = TASK_STATUS_COLORS.get(task.status, "gray")

        actions = []
        if task.id is None:
            return

        if task.status == TaskItemStatus.PLANNED:
            actions.append(("▶ Старт", partial(tb_system.start_task, task.id)))
        elif task.status == TaskItemStatus.IN_PROGRESS:
            actions.append(("⏸ Пауза", partial(tb_system.pause_task, task.id, "Оператор")))
            actions.append(
                (
                    "✓ Завершить",
                    partial(
                        tb_system.complete_task,
                        task.id,
                        sheets_done=task.sheet_qty or 0,
                    ),
                )
            )

        line2 = (
            f"{progress_str} | Узел: {task.assigned_to_node or '-'} | "
            f"Материал: {task.mat_type_id or '-'}"
        )
        if task.status == TaskItemStatus.DONE:
            pallets = tb_system.find_pallets_by_task(task.id, session)
            if pallets:
                pallet_labels = ", ".join(p.label_id for p in pallets)
                line2 += f" | 📦 Паллеты: {pallet_labels}"

        row = HierarchyRow(
            icon="description",
            title=task.file_name,
            badges=[(task.status.value, status_color)],
            line2=line2,
            actions=actions,
            indent=indent,
            system_scope=self.system_scope,
        )
        row.render()
