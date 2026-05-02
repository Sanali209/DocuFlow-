from collections.abc import Callable
from typing import Any

from nicegui import ui

from docuflow.lib.base_widget import BaseDocuWidget


class CompleteTaskDialog(BaseDocuWidget):
    """Dialog for completing a task with pallet selection."""

    def __init__(
        self,
        task_id: int,
        qty_produced: int,
        on_complete: Callable[..., None],
        existing_pallets: list[dict[str, Any]] | None = None,
        system_scope: Any = None,
    ) -> None:
        super().__init__(system_scope)
        self.task_id = task_id
        self.qty_produced = qty_produced
        self.on_complete = on_complete
        self.existing_pallets = existing_pallets or []
        self.create_new = True
        self.selected_pallet_id: int | None = None

    def open(self) -> None:
        """Open the completion dialog."""
        with ui.dialog() as dialog, ui.card().classes("p-6 gap-4 w-96"):
            ui.label("Завершить задачу").classes("text-lg font-bold")
            ui.label(f"Деталей произведено: {self.qty_produced}").classes("text-sm text-slate-400")

            # Radio selection
            self._new_radio = ui.radio(
                options={True: "Создать новую паллету", False: "Добавить к существующей"},
                value=True,
            ).classes("w-full")
            self._new_radio.on_value_change(self._on_radio_change)

            # Existing pallet selector (hidden by default)
            self._pallet_select = ui.select(
                label="Выберите паллету",
                options={p["id"]: p["label"] for p in self.existing_pallets},
                value=None,
            ).classes("w-full")
            self._pallet_select.set_visibility(False)

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Отмена", on_click=dialog.close).props("flat")

                def _confirm() -> None:
                    self.create_new = self._new_radio.value is True
                    self.selected_pallet_id = self._pallet_select.value
                    self.on_complete(
                        task_id=self.task_id,
                        create_new=self.create_new,
                        selected_pallet_id=self.selected_pallet_id,
                    )
                    dialog.close()

                ui.button("Завершить", on_click=_confirm).props("color=primary")

        dialog.open()

    def _on_radio_change(self, e: Any) -> None:
        is_new: bool = e.value is True
        self._pallet_select.set_visibility(not is_new)
