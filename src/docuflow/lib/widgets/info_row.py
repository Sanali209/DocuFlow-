"""
InfoRow - "label: value" row for displaying data.

Use for: details, properties, metadata.
"""

from typing import Any

from nicegui import ui


class InfoRow:
    """Строка информации.

    Args:
        label: str — лейбл (слева)
        value: str — значение (справа)
        value_color: str — цвет текста значения
        layout: str — "row" (label: value) или "col" (label сверху)
    """

    def __init__(
        self,
        label: str,
        value: str | Any,
        value_color: str = "text-white",
        layout: str = "row",
    ) -> None:
        self.label = label
        self.value = str(value) if value is not None else "-"
        self.value_color = value_color
        self.layout = layout

    def render(self) -> None:
        """Рендерит строку."""
        if self.layout == "col":
            with ui.column().classes("gap-1"):
                ui.label(self.label).classes("text-xs text-slate-400 font-medium")
                ui.label(self.value).classes(f"text-sm {self.value_color}")
        else:
            with ui.row().classes("w-full justify-between items-center"):
                ui.label(self.label).classes("text-sm text-slate-400")
                ui.label(self.value).classes(f"text-sm {self.value_color}")


class InfoGrid:
    """Сетка InfoRow.

    Args:
        rows: list[tuple[str, str]] — список (label, value)
    """

    def __init__(self, rows: list[tuple[str, str]] | None = None) -> None:
        self.rows = rows or []

    def render(self) -> None:
        """Рендерит сетку."""
        with ui.column().classes("w-full gap-2"):
            for label, value in self.rows:
                InfoRow(label, value).render()

    def add(self, label: str, value: str | Any) -> "InfoGrid":
        """Добавляет строку."""
        self.rows.append((label, str(value)))
        return self


class InfoPair:
    """Пара label: value в одну строку (alias).

    Args:
        label: str
        value: str
    """

    def __init__(self, label: str, value: str | Any) -> None:
        self.label = label
        self.value = value

    def render(self) -> None:
        """Рендерит пару."""
        InfoRow(self.label, self.value).render()
