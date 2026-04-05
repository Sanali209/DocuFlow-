from nicegui import ui

from docuflow.features.projects.system import ProjectSystem
from docuflow.features.work_items.system import WorkItemFilters, WorkItemSystem


class ProjectManagementView:
    """
    UI for managing projects and reassigning WorkItems from 'Default' to specific projects.

    Vertical Slice: features/projects/view.py
    """

    def __init__(self, project_system: ProjectSystem, work_item_system: WorkItemSystem):
        self.project_system = project_system
        self.wi_system = work_item_system
        self.selected_project_id: int | None = None

    def render(self):
        with ui.column().classes("w-full p-4 gap-6"):
            ui.label("Управление проектами").classes("text-h4 mb-2")

            with ui.row().classes("w-full gap-4"):
                # Left Column: Project List & Create
                with ui.card().classes("w-1/3 p-4"):
                    ui.label("Список проектов").classes("text-h6 mb-2")
                    self.projects_list = ui.column().classes("w-full gap-2")
                    self._refresh_projects()

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
                    self._refresh_work_items()

    def _refresh_projects(self):
        self.projects_list.clear()
        projects = self.project_system.get_all_active_projects()
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

    def _select_project(self, project_id: int):
        self.selected_project_id = project_id
        ui.notify(f"Выбран целевой проект ID {project_id}")
        self._refresh_projects()

    def _add_project(self):
        name = self.new_project_name.value.strip()
        if not name:
            ui.notify("Имя проекта не может быть пустым", type="warning")
            return
        # Use domain API to register a new project
        self.project_system.register_new_project(project_name=name)
        self.new_project_name.value = ""
        ui.notify(f"Проект '{name}' создан")
        self._refresh_projects()

    def _refresh_work_items(self):
        self.wi_table_container.clear()
        # Filter: only items in Default Project (resolve id from ProjectSystem)
        default_project = self.project_system.resolve_default_workshop_project()
        filters = WorkItemFilters(project_id=default_project.id, limit=500)
        items = self.wi_system.list(filters)

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

    def _reassign_item(self, wi_id: int):
        if not self.selected_project_id:
            ui.notify("Сначала выберите целевой проект в левой колонке", type="negative")
            return

        # Use ProjectSystem to determine the Default project id instead of hardcoded '1'
        try:
            default_project = self.project_system.resolve_default_workshop_project()
            default_id = default_project.id
        except Exception:
            # If resolution fails, fall back to legacy value but log/notify
            default_id = 1
            ui.notify("Не удалось определить проект Default; используется fallback ID=1", type="warning")

        if self.selected_project_id == default_id:
            ui.notify("Наряд уже находится в проекте Default", type="warning")
            return

        try:
            # Use domain API for reassignment
            self.project_system.reassign_production_group(
                work_item_id=wi_id, target_project_id=self.selected_project_id
            )
            ui.notify(f"Наряд {wi_id} переназначен")
            self._refresh_work_items()
        except Exception as e:
            ui.notify(f"Ошибка: {e}", type="negative")
