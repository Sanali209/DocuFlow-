"""
HandoverForm — collapsible form for shift handover.
"""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from docuflow.lib.base_widget import BaseDocuWidget


class HandoverForm(BaseDocuWidget):
    """Collapsible form for shift handover."""

    def __init__(
        self,
        node_id: str,
        on_submit: Callable[..., Any],
        system_scope: Any,
        on_toggle: Callable[[], Any] | None = None,
    ) -> None:
        super().__init__(system_scope)
        self.node_id = node_id
        self.on_submit = on_submit
        self.on_toggle = on_toggle
        self.is_visible = False

    def render(self) -> ui.column:
        with ui.column().classes("w-full gap-2") as container:
            with ui.row().classes("w-full justify-end"):
                toggle_label: str = "Свернуть ▲" if self.is_visible else "Сдать смену ▼"
                ui.button(toggle_label, on_click=self._toggle).props("flat color=orange")

            if self.is_visible:
                with ui.card().classes("w-full p-4 gap-3 bg-orange-50/5"):
                    ui.label(f"Передача смены на {self.node_id}").classes(
                        "text-sm font-bold text-orange-400"
                    )

                    self.recv_input = ui.input("Кому передаёте").classes("w-full")
                    self.note_input = ui.textarea("Заметка").classes("w-full")

                    with ui.row().classes("w-full justify-end gap-2"):
                        ui.button("Отмена", on_click=self._toggle).props("flat")
                        ui.button("ПОДТВЕРДИТЬ СДАЧУ", on_click=self._submit).props("color=orange")

        return container

    def _toggle(self) -> None:
        self.is_visible = not self.is_visible
        if self.on_toggle:
            self.on_toggle()

    async def _submit(self) -> None:
        recv: str = self.recv_input.value.strip() if hasattr(self, "recv_input") else ""
        note: str = self.note_input.value.strip() if hasattr(self, "note_input") else ""
        if not recv:
            ui.notify("Укажите кому сдаете смену", type="warning")
            return
        await self.on_submit(recv, note)
        self.is_visible = False
