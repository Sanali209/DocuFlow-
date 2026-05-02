"""
HandoverBanner — banner for incoming shift handover note.
"""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from docuflow.lib.base_widget import BaseDocuWidget


class HandoverBanner(BaseDocuWidget):
    """Banner for incoming shift handover note."""

    def __init__(
        self,
        from_operator: str,
        note: str,
        on_accept: Callable[[], Any],
        system_scope: Any,
    ) -> None:
        super().__init__(system_scope)
        self.from_operator = from_operator
        self.note = note
        self.on_accept = on_accept

    def render(self) -> ui.card:
        with ui.card().classes("w-full p-4 bg-orange-50 border-2 border-orange-200") as card:
            with ui.row().classes("items-center gap-2 mb-2"):
                ui.icon("info", color="orange").classes("text-2xl")
                ui.label("Заметка от предыдущей смены").classes("text-lg font-bold text-orange-800")

            ui.label(f"От: {self.from_operator}").classes("text-xs text-orange-600 mb-1")
            ui.label(self.note).classes(
                "text-body1 text-orange-900 mb-4 whitespace-pre-wrap italic"
            )

            with ui.row().classes("w-full justify-end"):
                ui.button("ПРИНЯТО", on_click=self.on_accept).props(
                    "color=orange rounded-xl"
                ).classes("font-bold")

        return card
