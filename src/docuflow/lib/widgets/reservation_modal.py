from typing import Any

from nicegui import ui
from sqlmodel import Session, select

from docuflow.domain.entities.production import MaterialStock, MaterialStockStatus
from docuflow.lib.base_widget import BaseDocuWidget


class ReservationModal(BaseDocuWidget):
    """Modal for reserving material for a TaskGroup."""

    def __init__(
        self,
        task_group_id: int,
        mat_type_id: int,
        on_reserve: Any,
        system_scope: Any,
    ) -> None:
        super().__init__(system_scope)
        self.task_group_id = task_group_id
        self.mat_type_id = mat_type_id
        self.on_reserve = on_reserve

    async def render(self) -> None:
        async with self.scope() as req:
            session: Session = await req.get(Session)
            stocks: list[MaterialStock] = list(
                session.exec(
                    select(MaterialStock).where(
                        MaterialStock.mat_type_id == self.mat_type_id,
                        MaterialStock.status == MaterialStockStatus.AVAILABLE,
                    )
                ).all()
            )

        with ui.dialog() as dialog, ui.card().classes("p-6 w-[450px] gap-4"):
            ui.label("Резервировать материал").classes("text-xl font-bold")

            if not stocks:
                ui.label("Нет доступных партий").classes("text-red-400")
            else:
                options: dict[int | None, str] = {
                    s.id: f"{s.batch_code or s.id} — {s.quantity} листов ({s.location or 'MAIN'})"
                    for s in stocks
                }
                self.stock_select = ui.select(options, label="Партия").classes("w-full")
                self.qty_input = ui.number("Количество листов", value=1, min=1).classes("w-full")
                self.type_select = ui.select(
                    {"soft": "Soft", "hard": "Hard"},
                    label="Тип резерва",
                    value="soft",
                ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Отмена", on_click=dialog.close).props("flat")
                ui.button("ЗАРЕЗЕРВИРОВАТЬ", on_click=lambda: self._reserve(dialog)).props(
                    "color=blue"
                )

        dialog.open()

    def _reserve(self, dialog: Any) -> None:
        stock_id: Any = self.stock_select.value if hasattr(self, "stock_select") else None
        qty: Any = self.qty_input.value if hasattr(self, "qty_input") else 0
        is_hard: bool = self.type_select.value == "hard" if hasattr(self, "type_select") else False
        if stock_id and qty > 0:
            self.on_reserve(stock_id, qty, is_hard)
            dialog.close()
