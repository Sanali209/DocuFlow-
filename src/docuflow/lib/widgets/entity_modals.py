from collections.abc import Callable
from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import (
    ProductionUnit,
    Project,
    TaskGroup,
    TaskItem,
    WorkItem,
)
from docuflow.lib.widgets.nest_preview import NestPreview


class ProjectModal:
    """Modal dialog for viewing and editing a Project."""

    def __init__(self, project: Project, on_save: Callable, system_scope: Any):
        self.project = project
        self.on_save = on_save
        self.system_scope = system_scope

    def render(self) -> None:
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[500px] gap-4"):
            ui.label(f"📁 Проект: {self.project.name}").classes("text-xl font-bold")
            self.name_input = ui.input("Название", value=self.project.name).classes("w-full")
            self.desc_input = ui.textarea("Описание", value=self.project.description or "").classes(
                "w-full"
            )
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Закрыть", on_click=dialog.close).props("flat")
                ui.button("Сохранить", on_click=lambda: self._save(dialog)).props("color=primary")
        dialog.open()

    def _save(self, dialog: ui.dialog) -> None:
        self.on_save(name=self.name_input.value, description=self.desc_input.value)
        dialog.close()


class WorkItemModal:
    """Modal dialog for viewing and editing a WorkItem."""

    def __init__(
        self,
        work_item: WorkItem,
        projects: list[Project],
        on_save: Callable,
        system_scope: Any,
    ):
        self.work_item = work_item
        self.projects = projects
        self.on_save = on_save
        self.system_scope = system_scope

    def render(self) -> None:
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[500px] gap-4"):
            ui.label(f"📂 Наряд: {self.work_item.folder_name}").classes("text-xl font-bold")

            self.folder_input = ui.input("Папка", value=self.work_item.folder_name).classes(
                "w-full"
            )
            self.sidra_input = ui.input(
                "SIDRA номер", value=self.work_item.sidra_number or ""
            ).classes("w-full")

            project_options = {p.name: p.id for p in self.projects}
            current_project = self.work_item.project.name if self.work_item.project else None
            self.project_select = ui.select(
                label="Проект",
                options=project_options,
                value=current_project,
            ).classes("w-full")

            ui.label("Группы задач:").classes("font-bold mt-2")
            for tg in self.work_item.task_groups or []:
                ui.label(f"• {tg.name or f'Группа {tg.id}'} ({len(tg.tasks)} задач)").classes(
                    "text-sm"
                )

            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Закрыть", on_click=dialog.close).props("flat")
                ui.button("Сохранить", on_click=lambda: self._save(dialog)).props("color=primary")
        dialog.open()

    def _save(self, dialog: ui.dialog) -> None:
        self.on_save(
            folder_name=self.folder_input.value,
            sidra_number=self.sidra_input.value,
            project_id=self.project_select.value,
        )
        dialog.close()


class TaskGroupModal:
    """Modal dialog for viewing a TaskGroup and assigning or splitting it."""

    def __init__(
        self,
        task_group: TaskGroup,
        nodes: list[str],
        on_assign: Callable,
        on_split: Callable,
        system_scope: Any,
    ):
        self.task_group = task_group
        self.nodes = nodes
        self.on_assign = on_assign
        self.on_split = on_split
        self.system_scope = system_scope

    def render(self) -> None:
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[500px] gap-4"):
            ui.label(
                f"📚 Группа: {self.task_group.name or f'Группа {self.task_group.id}'}"
            ).classes("text-xl font-bold")

            ui.label("Задачи:").classes("font-bold mt-2")
            for task in self.task_group.tasks or []:
                progress = task.sheets_done or 0
                total = task.sheet_qty or 0
                with ui.row().classes("w-full items-center gap-2"):
                    ui.label(f"{task.file_name}").classes("text-sm flex-grow")
                    ui.linear_progress(value=progress / total if total else 0).classes("w-24")
                    ui.label(f"{progress}/{total}").classes("text-xs")

            ui.separator()

            self.node_select = ui.select(
                label="Назначить на узел",
                options={n: n for n in self.nodes},
                value=None,
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Закрыть", on_click=dialog.close).props("flat")
                ui.button(
                    "Назначить",
                    on_click=lambda: self._assign(dialog),
                ).props("color=primary")
                ui.button(
                    "Разбить",
                    on_click=lambda: self._split(dialog),
                ).props("color=secondary")
        dialog.open()

    def _assign(self, dialog: ui.dialog) -> None:
        if self.node_select.value:
            self.on_assign(node_id=self.node_select.value)
        dialog.close()

    def _split(self, dialog: ui.dialog) -> None:
        self.on_split(task_group_id=self.task_group.id)
        dialog.close()


class TaskItemModal:
    """Modal dialog for viewing a TaskItem and performing actions."""

    def __init__(
        self,
        task_item: TaskItem,
        on_action: Callable | None = None,
        on_start: Callable[[int], None] | None = None,
        on_pause: Callable[[int], None] | None = None,
        on_complete: Callable[[int, bool, int | None], None] | None = None,
        on_incident: Callable[[int], None] | None = None,
        system_scope: Any = None,
    ):
        self.task_item = task_item
        self.on_action = on_action
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_complete = on_complete
        self.on_incident = on_incident
        self.system_scope = system_scope

    def render(self) -> None:
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[600px] gap-4"):
            ui.label(f"📄 Задача: {self.task_item.file_name}").classes("text-xl font-bold")

            with ui.row().classes("w-full gap-4"):
                ui.label(f"Статус: {self.task_item.status.value}").classes("text-sm")
                ui.label(f"Приоритет: {self.task_item.priority}").classes("text-sm")
                if self.task_item.is_urgent:
                    ui.badge("Срочно").props("color=red")

            ui.separator()

            with ui.grid(columns=2).classes("w-full gap-2"):
                ui.label("Материал:").classes("text-sm text-slate-400")
                ui.label(str(self.task_item.mat_type_id or "-")).classes("text-sm")

                ui.label("Листы:").classes("text-sm text-slate-400")
                ui.label(f"{self.task_item.sheets_done}/{self.task_item.sheet_qty or 0}").classes(
                    "text-sm"
                )

                ui.label("Размеры:").classes("text-sm text-slate-400")
                ui.label(
                    f"{self.task_item.sheet_x or '-'} x {self.task_item.sheet_y or '-'}"
                ).classes("text-sm")

                ui.label("Толщина:").classes("text-sm text-slate-400")
                ui.label(str(self.task_item.thickness or "-")).classes("text-sm")

                ui.label("Назначен узел:").classes("text-sm text-slate-400")
                ui.label(str(self.task_item.assigned_to_node or "-")).classes("text-sm")

            ui.separator()

            # Action buttons based on status
            with ui.row().classes("w-full justify-start gap-2"):
                if self.on_start and self.task_item.status.value == "planned":
                    ui.button("▶ Старт", on_click=lambda: self._start(dialog)).props("color=green")
                if self.on_pause and self.task_item.status.value == "in_progress":
                    ui.button("⏸ Пауза", on_click=lambda: self._pause(dialog)).props("color=orange")
                if self.on_complete and self.task_item.status.value in (
                    "in_progress",
                    "on_hold",
                ):
                    ui.button("✓ Завершить", on_click=lambda: self._complete(dialog)).props(
                        "color=primary"
                    )
                if self.on_incident:
                    ui.button("⚠️ Инцидент", on_click=lambda: self._incident(dialog)).props(
                        "color=negative"
                    )
                if self.on_action:
                    ui.button("Действие", on_click=lambda: self._action(dialog)).props(
                        "color=primary"
                    )

            ui.separator()

            ui.label("Превью раскроя:").classes("font-bold")
            if self.system_scope:
                preview = NestPreview(self.task_item, system_scope=self.system_scope)
                ui.timer(0.1, lambda: self._render_preview(preview), once=True)
            else:
                ui.label("Нет доступа к превью").classes("text-sm text-slate-400")

            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Закрыть", on_click=dialog.close).props("flat")
        dialog.open()

    def _render_preview(self, preview: NestPreview) -> None:
        async def _do() -> None:
            await preview.render()

        ui.timer(0.1, _do, once=True)

    def _action(self, dialog: ui.dialog) -> None:
        if self.on_action:
            self.on_action(task_item_id=self.task_item.id)
        dialog.close()

    def _start(self, dialog: ui.dialog) -> None:
        if self.on_start and self.task_item.id is not None:
            self.on_start(self.task_item.id)
        dialog.close()

    def _pause(self, dialog: ui.dialog) -> None:
        if self.on_pause and self.task_item.id is not None:
            self.on_pause(self.task_item.id)
        dialog.close()

    def _complete(self, dialog: ui.dialog) -> None:
        if self.on_complete and self.task_item.id is not None:
            self.on_complete(self.task_item.id, True, None)
        dialog.close()

    def _incident(self, dialog: ui.dialog) -> None:
        if self.on_incident and self.task_item.id is not None:
            self.on_incident(self.task_item.id)
        dialog.close()


class PalletModal:
    """Modal dialog for viewing a ProductionUnit (pallet) and shipping it."""

    def __init__(self, pallet: ProductionUnit, on_ship: Callable, system_scope: Any):
        self.pallet = pallet
        self.on_ship = on_ship
        self.system_scope = system_scope

    def render(self) -> None:
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[500px] gap-4"):
            ui.label(f"📦 Паллет: {self.pallet.label_id}").classes("text-xl font-bold")

            with ui.grid(columns=2).classes("w-full gap-2"):
                ui.label("Количество:").classes("text-sm text-slate-400")
                ui.label(str(self.pallet.qty_produced)).classes("text-sm")

                ui.label("Местоположение:").classes("text-sm text-slate-400")
                ui.label(
                    str(self.pallet.storage_location.code if self.pallet.storage_location else "-")
                ).classes("text-sm")

                ui.label("Связанная задача:").classes("text-sm text-slate-400")
                task_name = self.pallet.task_item.file_name if self.pallet.task_item else "-"
                ui.label(task_name).classes("text-sm")

                ui.label("На складе:").classes("text-sm text-slate-400")
                ui.label("Да" if self.pallet.is_stock else "Нет").classes("text-sm")

            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Закрыть", on_click=dialog.close).props("flat")
                ui.button(
                    "Отгрузить",
                    on_click=lambda: self._ship(dialog),
                ).props("color=primary")
        dialog.open()

    def _ship(self, dialog: ui.dialog) -> None:
        self.on_ship(pallet_id=self.pallet.id)
        dialog.close()
