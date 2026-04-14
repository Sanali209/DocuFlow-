"""
WorkItemsView — главный экран бригадира.

Список нарядов с фильтрацией, карточка наряда с деталями,
логом и кнопками действий.
"""

from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import (
    WorkItem,
    WorkItemStatus,
    WorkItemType,
)
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.view_presets.system import ViewPresetSystem
from docuflow.features.work_items.system import WorkItemFilters, WorkItemSystem
from docuflow.lib.widgets import StatusBadge
from docuflow.lib.widgets.work_item_card import WorkItemCard


def register_work_items_view():
    """Register the work items view in the global registry."""
    ViewRegistry.register(
        ViewInfo(
            name="work_items",
            label="Work Items",
            icon="work",
            render_fn=WorkItemsView,
            dependencies=[WorkItemSystem, ViewPresetSystem],
            pass_user=True,
            pass_switch_view=True,
            pass_system_provider=True,
        )
    )


class WorkItemsView:
    """
    Главный экран бригадира — список нарядов.

    Props:
        system: WorkItemSystem — система управления нарядами
        preset_system: ViewPresetSystem — система пресетов
        user: str — текущий пользователь
        on_navigate: callable — функция переключения экранов
    """

    def __init__(
        self,
        system: WorkItemSystem,
        preset_system: ViewPresetSystem,
        user: str = "admin",
        on_navigate: Any = None,
        system_provider: Any = None,
    ):
        self.system = system
        self.preset_system = preset_system
        self.user = user
        self.on_navigate = on_navigate
        self.system_provider = system_provider
        self.active_filters = WorkItemFilters()

    @ui.refreshable
    def render(self) -> None:
        """Рендерит основной view."""
        with ui.column().classes("w-full p-4"):
            self._render_filter_bar()
            self._render_preset_tabs()
            self._render_table()

    def _render_filter_bar(self) -> None:
        """Рендерит панель фильтров."""
        with ui.row().classes("gap-4 mb-4"):
            # Фильтр по статусу
            ui.select(
                options=[s.value for s in WorkItemStatus],
                label="Статус",
                multiple=True,
                on_change=lambda e: self._update_filters(status=e.value),
            ).classes("w-48")

            # Фильтр по типу
            ui.select(
                options=[t.value for t in WorkItemType],
                label="Тип",
                multiple=True,
                on_change=lambda e: self._update_filters(type=e.value),
            ).classes("w-32")

            # Поиск
            ui.input(
                label="Поиск",
                on_change=lambda e: self._update_filters(search_text=e.value),
            ).classes("w-64")

    def _render_preset_tabs(self) -> None:
        """Рендерит вкладки пресетов."""
        presets = self.preset_system.list("work_items", self.user)

        with ui.tabs().classes("w-full mb-4") as tabs:
            for preset in presets:
                # Store preset for reuse
                ui.tab(preset.name)

        tabs.on("change", lambda e: self._apply_preset(e.value))

    @ui.refreshable
    def _render_table(self) -> None:
        """Рендерит таблицу нарядов."""
        items = self.system.list_work_items_by_filter(self.active_filters)

        # Define Columns
        columns = [
            {"name": "status", "label": "Статус", "field": "status", "align": "center"},
            {"name": "folder_name", "label": "Папка", "field": "folder_name", "align": "left"},
            {"name": "sidra_number", "label": "Наряд №", "field": "sidra_number", "align": "left"},
            {
                "name": "work_item_type",
                "label": "Тип",
                "field": "work_item_type",
                "align": "center",
            },
            {
                "name": "doc_received_at",
                "label": "Документ",
                "field": "doc_received_at",
                "align": "center",
            },
        ]

        rows = [self._item_to_row(item) for item in items]

        with ui.table(
            columns=columns,
            rows=rows,
            on_select=lambda e: self._on_row_click(e.selection[0] if e.selection else None),
            selection="single",
            row_key="id",
        ).classes("w-full h-[600px]") as table:
            # Custom status column rendering
            table.add_slot(
                "body-cell-status",
                """
                <q-td :props="props">
                    <q-badge :color="props.row.status_color" :label="props.row.status_label" />
                </q-td>
            """,
            )

    def _item_to_row(self, item: WorkItem) -> dict:
        """Конвертирует WorkItem в строку таблицы."""
        badge = StatusBadge(item.status)
        return {
            "id": item.id,
            "status": item.status,
            "status_color": badge._get_color(),
            "status_label": badge._get_label(),
            "folder_name": item.folder_name,
            "sidra_number": item.sidra_number or "-",
            "work_item_type": item.work_item_type,
            "doc_received_at": item.doc_received_at.strftime("%d.%m.%Y")
            if item.doc_received_at
            else "-",
        }

    def _on_row_click(self, row: dict | None) -> None:
        """Обработка клика по строке."""
        if row:
            work_item = self.system.retrieve_work_item(row["id"])
            self._show_card(work_item)

    def _show_card(self, work_item: WorkItem) -> None:
        """Показывает карточку наряда используя глобальный виджет."""
        WorkItemCard(
            work_item,
            self.system,
            self.user,
            on_navigate=self.on_navigate,
            system_provider=self.system_provider,
        ).render()

    def _update_filters(self, **kwargs) -> None:
        """Обновляет фильтры и обновляет таблицу."""
        for key, value in kwargs.items():
            if hasattr(self.active_filters, key):
                # Convert string values from UI back to Enums if needed
                if key == "status" and value:
                    setattr(self.active_filters, key, [WorkItemStatus(v) for v in value])
                elif key == "type" and value:
                    setattr(self.active_filters, key, [WorkItemType(v) for v in value])
                else:
                    setattr(self.active_filters, key, value)

        self._render_table.refresh()

    def _apply_preset(self, preset_name: str) -> None:
        """Применяет пресет."""
        presets = self.preset_system.list("work_items", self.user)
        preset = next((p for p in presets if p.name == preset_name), None)

        if preset:
            config = self.preset_system.get_preset_json(preset)
            filters = config.get("filters", {})

            if "status" in filters:
                self.active_filters.status = [WorkItemStatus(s) for s in filters["status"]]

            if "type" in filters:
                self.active_filters.type = [WorkItemType(t) for t in filters["type"]]
