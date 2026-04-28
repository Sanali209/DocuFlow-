import json
from collections.abc import Callable
from typing import Any

from nicegui import ui

from docuflow.lib.base_widget import BaseDocuWidget


class FilterPanel(BaseDocuWidget):
    """Collapsible filter panel with presets support."""

    def __init__(
        self,
        on_apply: Callable[[dict[str, Any]], None],
        system_scope: Any = None,
        initial_filters: dict[str, Any] | None = None,
        presets: list[dict[str, Any]] | None = None,
        on_save_preset: Callable[[str, dict[str, Any]], None] | None = None,
    ):
        super().__init__(system_scope)
        self.on_apply = on_apply
        self.filters: dict[str, Any] = initial_filters or {}
        self.presets: list[dict[str, Any]] = presets or []
        self.on_save_preset = on_save_preset

    def render(self) -> None:
        """Render the filter panel UI."""
        with ui.card().classes("w-full p-4 bg-white/5 rounded-2xl border border-white/10"):
            with ui.row().classes("w-full items-center justify-between mb-4"):
                ui.label("Фильтры").classes("text-sm font-bold text-indigo-300")
                ui.button("Свернуть", on_click=self._toggle_visibility).props(
                    "flat dense size=sm"
                ).classes("text-xs")

            # Presets selector
            if self.presets:
                preset_options = {p["id"]: p["name"] for p in self.presets}
                ui.select(
                    label="Пресет",
                    options=preset_options,
                    on_change=self._load_preset,
                ).classes("w-48")

            # Project filter
            self._project_select = ui.select(
                label="Проект", options={}, value=self.filters.get("project_id")
            ).classes("w-48")

            # Status filters
            with ui.row().classes("gap-4"):
                self._status_select = ui.select(
                    label="Статус задачи",
                    options={
                        "planned": "PLANNED",
                        "in_progress": "IN_PROGRESS",
                        "done": "DONE",
                        "on_hold": "ON_HOLD",
                        "suspended": "SUSPENDED",
                    },
                    value=self.filters.get("status"),
                ).classes("w-48")

                self._urgent_switch = ui.switch(
                    "Только срочные", value=self.filters.get("urgent", False)
                )

            # Node filter
            self._node_select = ui.select(label="Узел", options={}).classes("w-48")

            # Action buttons
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Сбросить", on_click=self._reset).props("flat")
                ui.button("Применить", on_click=self._apply).props("color=primary")
                ui.button("💾 Сохранить пресет", on_click=self._save_preset).props("outline")

    def _toggle_visibility(self) -> None:
        pass

    def _load_preset(self, e: Any) -> None:
        """Load a preset by ID and apply its filters."""
        preset_id = e.value
        if preset_id is None:
            return
        for p in self.presets:
            if p["id"] == preset_id:
                try:
                    loaded = json.loads(p.get("filters_json", "{}"))
                    self.filters = loaded
                    self.on_apply(self.filters)
                except json.JSONDecodeError:
                    ui.notify("Ошибка загрузки пресета", type="negative")
                return

    def _apply(self) -> None:
        """Collect current filter values and trigger on_apply."""
        if hasattr(self, "_project_select"):
            self.filters = {
                "project_id": self._project_select.value,
                "status": self._status_select.value,
                "urgent": self._urgent_switch.value,
                "node": self._node_select.value,
            }
            # Remove None values
            self.filters = {k: v for k, v in self.filters.items() if v is not None}
        self.on_apply(self.filters)

    def _reset(self) -> None:
        """Clear all filters and trigger on_apply with empty dict."""
        self.filters = {}
        if hasattr(self, "_project_select"):
            self._project_select.set_value(None)
            self._status_select.set_value(None)
            self._urgent_switch.set_value(False)
            self._node_select.set_value(None)
        self.on_apply(self.filters)

    def _save_preset(self) -> None:
        """Open dialog to save current filters as a preset."""
        if self.on_save_preset:
            with ui.dialog() as dialog, ui.card().classes("p-4 gap-4 w-80"):
                ui.label("Сохранить пресет").classes("text-lg font-bold")
                name_input = ui.input("Название пресета").classes("w-full")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Отмена", on_click=dialog.close).props("flat")

                    def _confirm() -> None:
                        if name_input.value and self.on_save_preset is not None:
                            self.on_save_preset(name_input.value, self.filters)
                            dialog.close()
                            ui.notify("Пресет сохранён", type="positive")

                    ui.button("Сохранить", on_click=_confirm).props("color=primary")
            dialog.open()
        else:
            ui.notify("Сохранение пресетов недоступно", type="warning")
