from collections.abc import Callable
from typing import Any

from nicegui import ui

from docuflow.lib.base_widget import BaseDocuWidget


class HierarchyRow(BaseDocuWidget):
    """Two-line hierarchy row with expand/collapse and actions."""

    def __init__(
        self,
        icon: str,
        title: str,
        badges: list[tuple[str, str]] | None = None,
        line2: str = "",
        actions: list[tuple[str, Callable[[], None]]] | None = None,
        is_expandable: bool = False,
        is_expanded: bool = True,
        on_toggle: Callable[[bool], None] | None = None,
        indent: int = 0,
        system_scope: Any = None,
    ) -> None:
        super().__init__(system_scope)
        self.icon = icon
        self.title = title
        self.badges = badges or []
        self.line2 = line2
        self.actions = actions or []
        self.is_expandable = is_expandable
        self.is_expanded = is_expanded
        self.on_toggle = on_toggle
        self.indent = indent

    def render(self) -> ui.row:
        """Render the row and return the root element."""
        with ui.row().classes("w-full items-start gap-2") as row:
            # Indent
            if self.indent > 0:
                ui.space().classes(f"w-{self.indent * 4}")

            # Expand/collapse toggle
            if self.is_expandable:
                toggle_icon = "expand_less" if self.is_expanded else "expand_more"
                ui.button(icon=toggle_icon, on_click=self._toggle).props("flat dense size=sm")
            else:
                ui.space().classes("w-6")

            # Icon
            ui.icon(self.icon, size="20px").classes("mt-1 text-slate-400")

            # Content
            with ui.column().classes("flex-grow gap-0"):
                # Line 1: Title + badges
                with ui.row().classes("items-center gap-2"):
                    ui.label(self.title).classes("font-medium text-white")
                    for text, color in self.badges:
                        ui.badge(text).props(f"color={color} size=xs")

                # Line 2: Metadata + actions
                with ui.row().classes("items-center gap-2"):
                    if self.line2:
                        ui.label(self.line2).classes("text-xs text-slate-500")
                    for label, callback in self.actions:
                        ui.button(label, on_click=callback).props("flat dense size=xs").classes(
                            "text-xs"
                        )

        return row

    def _toggle(self) -> None:
        self.is_expanded = not self.is_expanded
        if self.on_toggle:
            self.on_toggle(self.is_expanded)
