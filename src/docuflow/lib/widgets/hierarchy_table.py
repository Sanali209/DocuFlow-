import asyncio
from functools import partial
from typing import Any

from nicegui import ui
from sqlmodel import Session, select

from docuflow.domain.entities.production import (
    Project,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
    TaskPart,
    ViewState,
    WorkItem,
)
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.task_board.task_group_service import TaskGroupService
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.complete_task_dialog import CompleteTaskDialog
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

    @ui.refreshable
    async def render(self) -> None:
        with ui.column().classes("w-full gap-2"):
            async with self.scope() as req:
                session = await req.get(Session)
                tb_system = await req.get(TaskBoardSystem)

                if self.filters.get("project_id"):
                    project = session.get(Project, self.filters["project_id"])
                    projects = [project] if project else []
                else:
                    projects = list(session.exec(select(Project)).all())

                for project in projects:
                    self._render_project(session, tb_system, project)

    def _render_project(
        self, session: Session, tb_system: TaskBoardSystem, project: Project
    ) -> None:
        work_items = list(
            session.exec(select(WorkItem).where(WorkItem.project_id == project.id)).all()
        )

        is_expanded = self._get_expansion_state(session, "project", project.id or 0)

        def toggle(expanded: bool) -> None:
            async def _save() -> None:
                async with self.scope() as req:
                    s = await req.get(Session)
                    self._save_expansion_state(s, "project", project.id or 0, expanded)

            asyncio.get_event_loop().create_task(_save())

        row = HierarchyRow(
            icon="folder",
            title=project.name,
            badges=[(f"{len(work_items)} нарядов", "blue")],
            line2=project.description or "",
            is_expandable=True,
            is_expanded=is_expanded,
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
        is_expanded = self._get_expansion_state(session, "workitem", wi.id or 0)

        def toggle(expanded: bool) -> None:
            async def _save() -> None:
                async with self.scope() as req:
                    s = await req.get(Session)
                    self._save_expansion_state(s, "workitem", wi.id or 0, expanded)

            asyncio.get_event_loop().create_task(_save())

        row = HierarchyRow(
            icon="inventory_2",
            title=wi.folder_name,
            badges=[(wi.status.value, "gray"), (f"{total_tasks} задач", "teal")],
            line2=(
                f"SIDRA: {wi.sidra_number or '-'} | "
                f"Проект: {wi.project.name if wi.project else '-'}"
            ),
            is_expandable=True,
            is_expanded=is_expanded,
            actions=[("Редактировать", lambda: None)],
            indent=indent,
            system_scope=self.system_scope,
        )
        row.render()

        if row.is_expanded:
            all_projects = list(session.exec(select(Project)).all())
            project_options = {p.id: p.name for p in all_projects if p.id != wi.project_id}

            def do_move(project_id: int) -> None:
                if project_id is None:
                    return
                assert wi.id is not None
                tb_system.move_work_item_to_project(wi.id, project_id)
                ui.notify(
                    f"Перемещено в {project_options.get(project_id, 'проект')}",
                    type="positive",
                )
                self.render.refresh()

            with ui.row().classes("gap-2 items-center ml-12 mb-2"):
                ui.label("Переместить в проект:").classes("text-xs text-slate-400")
                ui.select(
                    options=project_options,
                    on_change=lambda e: do_move(e.value),
                    label="Выберите проект",
                ).classes("w-56")

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

        is_expanded = self._get_expansion_state(session, "taskgroup", tg.id or 0)

        def toggle(expanded: bool) -> None:
            async def _save() -> None:
                async with self.scope() as req:
                    s = await req.get(Session)
                    self._save_expansion_state(s, "taskgroup", tg.id or 0, expanded)

            asyncio.get_event_loop().create_task(_save())

        row = HierarchyRow(
            icon="layers",
            title=tg.name or f"Группа {tg.id}",
            badges=[(f"{len(tg.tasks)} задач", status_color), (status, status_color)],
            line2=line2,
            is_expandable=True,
            is_expanded=is_expanded,
            indent=indent,
            system_scope=self.system_scope,
        )
        row.render()

        if row.is_expanded:
            nodes = ["node1", "node2", "node3"]  # TODO: load from config

            def do_assign(node_id: str) -> None:
                if node_id is None:
                    return
                assert tg.id is not None
                tb_system.assign_task_group_to_node(tg.id, node_id)
                ui.notify(f"Назначено на {node_id}", type="positive")
                self.render.refresh()

            with ui.row().classes("gap-2 items-center ml-12 mb-2"):
                ui.label("Назначить на узел:").classes("text-xs text-slate-400")
                ui.select(
                    options={n: n for n in nodes},
                    on_change=lambda e: do_assign(e.value),
                    label="Выберите узел",
                ).classes("w-56")

            for task in tg.tasks:
                self._render_taskitem(session, tb_system, task, indent=indent + 1)

    def _get_expansion_state(self, session: Session, entity_type: str, entity_id: int) -> bool:
        """Load expansion state from ViewState or default to True."""
        vs = session.exec(
            select(ViewState).where(
                ViewState.user_id == self.user_id,
                ViewState.view_name == self.view_name,
                ViewState.entity_type == entity_type,
                ViewState.entity_id == str(entity_id),
            )
        ).first()
        return vs.is_expanded if vs is not None else True

    def _save_expansion_state(
        self, session: Session, entity_type: str, entity_id: int, is_expanded: bool
    ) -> None:
        """Persist expansion state to ViewState."""
        vs = session.exec(
            select(ViewState).where(
                ViewState.user_id == self.user_id,
                ViewState.view_name == self.view_name,
                ViewState.entity_type == entity_type,
                ViewState.entity_id == str(entity_id),
            )
        ).first()
        if vs is not None:
            vs.is_expanded = is_expanded
        else:
            vs = ViewState(
                user_id=self.user_id,
                view_name=self.view_name,
                entity_type=entity_type,
                entity_id=str(entity_id),
                is_expanded=is_expanded,
            )
            session.add(vs)
        session.commit()

    def _render_taskitem(
        self, session: Session, tb_system: TaskBoardSystem, task: TaskItem, indent: int
    ) -> None:
        progress_str = f"{task.sheets_done}/{task.sheet_qty} листов"

        status_color = TASK_STATUS_COLORS.get(task.status, "gray")

        actions = []
        if task.id is None:
            return
        task_id: int = task.id

        if task.status == TaskItemStatus.PLANNED:
            actions.append(("▶ Старт", partial(tb_system.start_task, task_id)))
        elif task.status == TaskItemStatus.IN_PROGRESS:
            actions.append(("⏸ Пауза", partial(tb_system.pause_task, task_id, "Оператор")))

            def _open_complete_dialog() -> None:
                existing = tb_system.find_pallets_by_task(task_id, session)
                pallet_options = [
                    {"id": p.id, "label": p.label_id} for p in existing if p.id is not None
                ]

                def _on_complete(**kwargs: Any) -> None:
                    create_new = kwargs.get("create_new", True)
                    selected_id = kwargs.get("selected_pallet_id")
                    if create_new:
                        tb_system.complete_task(
                            task_id, sheets_done=task.sheet_qty or 0, create_pallet=True
                        )
                    else:
                        tb_system.complete_task(
                            task_id, sheets_done=task.sheet_qty or 0, create_pallet=False
                        )
                        if selected_id:
                            # TODO: add qty to existing pallet
                            pass
                    self.render.refresh()

                CompleteTaskDialog(
                    task_id=task_id,
                    qty_produced=task.qty_produced or 0,
                    on_complete=_on_complete,
                    existing_pallets=pallet_options,
                    system_scope=self.system_scope,
                ).open()

            actions.append(("✓ Завершить", _open_complete_dialog))
            actions.append(
                (
                    "⚠️ Инцидент",
                    lambda: ui.notify(f"Инцидент по задаче #{task_id}", type="negative"),
                )
            )

        line2 = (
            f"{progress_str} | Узел: {task.assigned_to_node or '-'} | "
            f"Материал: {task.mat_type_id or '-'}"
        )
        if task.status == TaskItemStatus.DONE:
            pallets = tb_system.find_pallets_by_task(task_id, session)
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

        # Show parts with deeplink to Part Library
        parts = list(session.exec(select(TaskPart).where(TaskPart.task_item_id == task_id)).all())
        if parts:
            with ui.row().classes(f"gap-2 items-center ml-{12 + indent * 4} mb-1"):
                ui.label("Детали:").classes("text-xs text-slate-400")
                for part in parts:
                    ui.button(
                        f"{part.part_sku} (x{part.qty})",
                        on_click=lambda sku=part.part_sku: ui.navigate.to(f"/parts?sku={sku}"),
                    ).props("flat dense size=xs").classes("text-xs text-blue-400")
