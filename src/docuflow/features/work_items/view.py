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
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets import StatusBadge
from docuflow.lib.widgets.work_item_card import WorkItemCard


def register_work_items_view():
    """Register the work items view in the global registry."""
    ViewRegistry.register(
        ViewInfo(
            name="work_items",
            label="Work Items",
            icon="work",
            render_fn=work_items_view_wrapper,
            dependencies=[WorkItemSystem, ViewPresetSystem],
            pass_user=True,
            pass_switch_view=True,
            pass_system_scope=True,
            is_async=True,
        )
    )


async def work_items_view_wrapper(
    wi_system: WorkItemSystem,
    preset_system: ViewPresetSystem,
    user: str,
    on_navigate: Any,
    system_scope: Any,
    **kwargs,
):
    """Wrapper to instantiate and render the WorkItemsView."""
    view = WorkItemsView(wi_system, preset_system, user, on_navigate, system_scope, **kwargs)
    await view.render()


class WorkItemsView(BaseDocuWidget):
    """
    Главный экран бригадира — список нарядов.
    """

    def __init__(
        self,
        system: WorkItemSystem,
        preset_system: ViewPresetSystem,
        user: str = "admin",
        on_navigate: Any = None,
        system_scope: Any = None,
        **kwargs,
    ):
        super().__init__(system_scope)
        self.system = system
        self.preset_system = preset_system
        self.user = user
        self.on_navigate = on_navigate
        self.active_filters = WorkItemFilters()
        if "filter_text" in kwargs:
            self.active_filters.search_text = kwargs["filter_text"]

    async def render(self) -> None:
        """Рендерит основной view."""
        with ui.column().classes("w-full p-4"):
            await self._render_filter_bar()
            await self._render_preset_tabs()
            await self._render_table()

    async def _render_filter_bar(self) -> None:
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

    async def _render_preset_tabs(self) -> None:
        """Рендерит вкладки пресетов."""
        async with self.scope() as req:
            p_sys = await req.get(ViewPresetSystem)
            presets = p_sys.list("work_items", self.user)

            with ui.tabs().classes("w-full mb-4") as tabs:
                for preset in presets:
                    ui.tab(preset.name)

            tabs.on_value_change(lambda e: self._apply_preset(e.value))

    @ui.refreshable_method
    async def _render_table(self) -> None:
        """Рендерит таблицу нарядов."""
        async with self.scope() as req:
            wi_sys = await req.get(WorkItemSystem)
            items = wi_sys.list_work_items_by_filter(self.active_filters)

            # Define Columns
            columns = [
                {"name": "status", "label": "Статус", "field": "status", "align": "center"},
                {"name": "folder_name", "label": "Папка", "field": "folder_name", "align": "left"},
                {
                    "name": "sidra_number",
                    "label": "Наряд №",
                    "field": "sidra_number",
                    "align": "left",
                },
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

    async def _on_row_click(self, row: dict | None) -> None:
        """Обработка клика по строке."""
        if row:
            async with self.scope() as req:
                wi_sys = await req.get(WorkItemSystem)
                work_item = wi_sys.retrieve_work_item(row["id"])
                await self._show_card(work_item)

    async def _show_card(self, work_item: WorkItem) -> None:
        """Показывает карточку наряда используя глобальный виджет."""
        await WorkItemCard(
            work_item,
            None,  # system is resolved inside
            self.user,
            on_navigate=self.on_navigate,
            system_scope=self.system_scope,
        ).render()

    async def _update_filters(self, **kwargs) -> None:
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

        await self._render_table.refresh()

    async def _apply_preset(self, preset_name: str) -> None:
        """Применяет пресет."""
        async with self.scope() as req:
            p_sys = await req.get(ViewPresetSystem)
            presets = p_sys.list("work_items", self.user)
            preset = next((p for p in presets if p.name == preset_name), None)

            if preset:
                config = p_sys.get_preset_json(preset)
                filters = config.get("filters", {})

                if "status" in filters:
                    self.active_filters.status = [WorkItemStatus(s) for s in filters["status"]]

                if "type" in filters:
                    self.active_filters.type = [WorkItemType(t) for t in filters["type"]]

                await self._render_table.refresh()
