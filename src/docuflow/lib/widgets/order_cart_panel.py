from collections.abc import Callable
from functools import partial
from typing import Any

from nicegui import ui

from docuflow.features.parts.order_cart import OrderCart
from docuflow.lib.base_widget import BaseDocuWidget


class OrderCartPanel(BaseDocuWidget):
    """Collapsible order cart panel for Part Library."""

    def __init__(
        self,
        cart: OrderCart,
        on_create_order: Callable[..., Any],
        system_scope: Any,
    ) -> None:
        super().__init__(system_scope)
        self.cart = cart
        self.on_create_order = on_create_order
        self.is_visible = False

    @ui.refreshable
    def render(self) -> None:
        with ui.column().classes("w-full"):
            count: int = len(self.cart.get_items())
            arrow: str = "▼" if self.is_visible else "▲"
            label: str = f"🛒 Корзина ({count}) {arrow}"
            ui.button(label, on_click=self._toggle).props("flat color=primary")

            if self.is_visible and not self.cart.is_empty():
                with ui.card().classes("w-full p-4 gap-2"):
                    for item in self.cart.get_items():
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(f"{item.sku} — {item.name or ''}").classes("text-sm")
                            ui.number(
                                value=item.qty,
                                min=1,
                                on_change=partial(self._update_qty, item.sku),
                            ).classes("w-20")
                            ui.button("✕", on_click=partial(self._remove, item.sku)).props(
                                "flat dense size=xs color=red"
                            )

                    with ui.row().classes("w-full justify-end gap-2 mt-2"):
                        ui.button("Очистить", on_click=self._clear).props("flat")
                        ui.button(
                            "СОЗДАТЬ ЗАКАЗ ▼",
                            on_click=self._show_order_form,
                        ).props("color=primary")

    def _toggle(self) -> None:
        self.is_visible = not self.is_visible
        self.render.refresh()

    def _update_qty(self, sku: str, sender: Any) -> None:
        try:
            qty: int = int(sender.value) if sender.value is not None else 1
        except (ValueError, TypeError):
            qty = 1
        self.cart.update_qty(sku, qty)
        self.render.refresh()

    def _remove(self, sku: str) -> None:
        self.cart.remove(sku)
        self.render.refresh()

    def _clear(self) -> None:
        self.cart.clear()
        self.render.refresh()

    def _show_order_form(self) -> None:
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[400px] gap-4"):
            ui.label("Создать заказ (Rework)").classes("text-xl font-bold")
            order_name_input: ui.input = ui.input("Название Sidra", value="REWORK-001").classes(
                "w-full"
            )
            ui.label("Детали в заказе:").classes("text-sm text-slate-500")
            for item in self.cart.get_items():
                ui.label(f"• {item.sku} — {item.qty} шт").classes("text-sm")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Отмена", on_click=dialog.close).props("flat")
                ui.button(
                    "СОЗДАТЬ",
                    on_click=lambda d=dialog, inp=order_name_input: self._create_order(d, inp),
                ).props("color=primary")
        dialog.open()

    async def _create_order(self, dialog: Any, order_name_input: Any) -> None:
        name: str = order_name_input.value.strip() if order_name_input else "REWORK-001"
        await self.on_create_order(name, self.cart.get_items())
        dialog.close()
        self.cart.clear()
        self.render.refresh()
