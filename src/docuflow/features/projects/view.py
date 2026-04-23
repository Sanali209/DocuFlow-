from typing import Any

from nicegui import ui

from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.projects.system import ProjectSystem
from docuflow.features.work_items.system import WorkItemFilters, WorkItemSystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper


def register_projects_view():
    """Register the projects management view."""
    ViewRegistry.register(
        ViewInfo(
            name="projects",
            label="Projects",
            icon="topic",
            render_fn=projects_view_wrapper,
            dependencies=[ProjectSystem, WorkItemSystem],
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def projects_view_wrapper(
    project_system: ProjectSystem, wi_system: WorkItemSystem, system_scope: Any, layout: Any, **kwargs
):
    """Wrapper to instantiate and render the ProjectManagementView."""
    await ProjectManagementView(project_system, wi_system, system_scope, layout=layout).render()


class ProjectManagementView(BaseDocuWidget):
    """
    UI for managing projects and reassigning WorkItems from 'Default' to specific projects.
    """

    def __init__(
        self,
        project_system: ProjectSystem,
        work_item_system: WorkItemSystem,
        system_scope: Any,
        layout: Any = None,
    ):
        super().__init__(system_scope)
        self.project_system = project_system
        self.wi_system = work_item_system
        self.layout = layout
        self.selected_project_id: int | None = None

    async def render(self):
        with ui.column().classes("w-full p-4 gap-6"):
            ui.label("Управление проектами").classes("text-h4 mb-2")

            with ui.row().classes("w-full gap-4"):
                # Left Column: Project List & Create
                with ui.card().classes("w-1/3 p-4"):
                    ui.label("Список проектов").classes("text-h6 mb-2")
                    self.projects_list = ui.column().classes("w-full gap-2")
                    await self._refresh_projects()

                    ui.separator().classes("my-4")

                    with ui.row().classes("items-center gap-2"):
                        self.new_project_name = ui.input("Имя нового проекта").classes("flex-grow")
                        ui.button(icon="add", on_click=self._add_project).props(
                            "round color=primary"
                        )

                # Right Column: Reassignment Area
                with ui.card().classes("w-2/3 p-4"):
                    ui.label("Переназначение нарядов (из Default)").classes("text-h6 mb-2")
                    ui.markdown(
                        "Выберите наряды в левой колонке (из проекта Default) и назначьте их в целевой проект."
                    )

                    self.wi_table_container = ui.column().classes("w-full")
                    await self._refresh_work_items()

    async def _refresh_projects(self):
        self.projects_list.clear()
        async with self.scope() as req:
            p_sys = await req.get(ProjectSystem)
            projects = p_sys.get_all_active_projects()

            with self.projects_list:
                for p in projects:
                    with ui.row().classes(
                        "w-full items-center justify-between p-2 hover:bg-blue-50 cursor-pointer rounded"
                    ):
                        ui.label(p.name).classes("font-bold")
                        if p.is_default:
                            ui.badge("Default", color="gray")
                        else:
                            ui.label(f"ID: {p.id}").classes("text-xs text-gray-400")

                        # Highlight selected project for reassignment
                        if self.selected_project_id == p.id:
                            ui.button(icon="check", color="success").props("flat round")
                        else:
                            ui.button(
                                icon="login", on_click=lambda p=p: self._select_project(p.id)
                            ).props("flat round")

    async def _select_project(self, project_id: int):
        self.selected_project_id = project_id
        NotifyHelper.warning(f"Выбран целевой проект ID {project_id}")
        await self._refresh_projects()

    async def _add_project(self):
        name = self.new_project_name.value.strip()
        if not name:
            NotifyHelper.error("Имя проекта не может быть пустым")
            return

        # Use fresh system from provider to avoid DetachedInstanceError
        async with self.scope() as req:
            sys = await req.get(ProjectSystem)
            sys.register_new_project(project_name=name)

        self.new_project_name.value = ""
        NotifyHelper.warning(f"Проект '{name}' создан")
        await self._refresh_projects()

    async def _refresh_work_items(self):
        self.wi_table_container.clear()

        async with self.scope() as req:
            # Consolidate system resolution
            p_sys = await req.get(ProjectSystem)
            wi_sys = await req.get(WorkItemSystem)

            # Filter: only items in Default Project (resolve id from ProjectSystem)
            default_project = p_sys.resolve_default_workshop_project()
            filters = WorkItemFilters(project_id=default_project.id, limit=500)
            items = wi_sys.list_work_items_by_filter(filters)

            if not items:
                with self.wi_table_container:
                    ui.label("Нет нарядов в проекте Default").classes("text-gray-400 mt-4 italic")
                return

            columns = [
                {"name": "folder_name", "label": "Папка", "field": "folder_name", "align": "left"},
                {"name": "status", "label": "Статус", "field": "status", "align": "center"},
                {"name": "action", "label": "Действие", "field": "action", "align": "right"},
            ]

            rows = [
                {
                    "id": item.id,
                    "folder_name": item.folder_name,
                    "status": item.status,
                }
                for item in items
            ]

            with self.wi_table_container:
                self.table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
                self.table.add_slot(
                    "body-cell-action",
                    """
                    <q-td :props="props">
                        <q-btn flat round color="primary" icon="move_to_inbox" @click="() => $emit('reassign', props.row.id)" />
                    </q-td>
                """,
                )
                self.table.on("reassign", lambda e: self._reassign_item(e.args))

    async def _reassign_item(self, wi_id: int):
        if not self.selected_project_id:
            NotifyHelper.info("Сначала выберите целевой проект в левой колонке")
            return

        async with self.scope() as req:
            # Use fresh system
            p_sys = await req.get(ProjectSystem)
            default_project = p_sys.resolve_default_workshop_project()
            default_id = default_project.id

            if self.selected_project_id == default_id:
                NotifyHelper.error("Наряд уже находится в проекте Default")
                return

            try:
                # Use domain API for reassignment
                p_sys.reassign_production_group(
                    work_item_id=wi_id, target_project_id=self.selected_project_id
                )
                NotifyHelper.info(f"Наряд {wi_id} переназначен")
                await self._refresh_work_items()
            except Exception as e:
                NotifyHelper.info(f"Ошибка: {e}")
