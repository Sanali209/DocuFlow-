from typing import Any

from nicegui import ui
from sqlmodel import select

from docuflow.domain.entities.production import ProductionUnit
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.production.system import ProductionSystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper


def register_production_view():
    """Register the production management view."""
    ViewRegistry.register(
        ViewInfo(
            name="production",
            label="Production",
            icon="precision_manufacturing",
            render_fn=production_view_wrapper,
            pass_user=True,
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def production_view_wrapper(user: str, system_scope: Any, layout: Any, **kwargs) -> None:
    """Wrapper to instantiate and render the ProductionView."""
    view = ProductionView(user, system_scope, layout=layout)
    await view.render()


class ProductionView(BaseDocuWidget):
    """Provides the UI for managing production pallets (ProductionUnit)."""

    def __init__(self, user: str, system_scope: Any, layout: Any = None):
        super().__init__(system_scope)
        self.user = user
        self.layout = layout
        self.grid: Any = None
        self.search_term: Any = None

    async def render(self) -> None:
        """Render the production management dashboard."""
        with ui.column().classes("w-full h-full p-4 gap-4"):
            ui.label("Управление Паллетами (Склад готовой продукции)").classes(
                "text-3xl font-bold text-white mb-2"
            )

            self.search_term = (
                ui.input("Поиск по номеру (label_id)")
                .props("dark standout rounded")
                .classes("w-64")
            )

            grid_cols = [
                {"name": "id", "label": "ID", "field": "id", "align": "left"},
                {
                    "name": "label_id",
                    "label": "Номер (Label)",
                    "field": "label_id",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "qty_produced",
                    "label": "Кол-во",
                    "field": "qty_produced",
                    "align": "center",
                },
                {
                    "name": "parent_label_id",
                    "label": "Родитель",
                    "field": "parent_label_id",
                    "align": "center",
                },
                {"name": "created_by", "label": "Создал", "field": "created_by", "align": "center"},
                {"name": "status", "label": "Статус", "field": "status", "align": "center"},
                {"name": "actions", "label": "", "field": "id", "align": "right"},
            ]

            self.grid = ui.table(
                columns=grid_cols, rows=[], row_key="id", selection="multiple"
            ).classes("w-full glass-card text-white")
            self.grid.add_slot(
                "body-cell-status",
                """
                <q-td :props="props">
                    <q-badge :color="props.row.status_color" :label="props.row.status_label" />
                </q-td>
            """,
            )
            self.grid.add_slot(
                "body-cell-actions",
                """
                <q-td :props="props">
                    <q-btn flat round dense color="indigo" icon="local_shipping"
                        @click="$parent.$emit('ship', props.row)" v-if="props.row.can_ship" />
                    <q-btn flat round dense color="orange" icon="call_split"
                        @click="$parent.$emit('split', props.row)" />
                </q-td>
            """,
            )

            self.search_term.on_value_change(self.refresh_grid)
            self.grid.on("ship", lambda e: self.handle_shipment(e.args))

            # Split Dialog
            with ui.dialog().classes("glass-card p-6") as split_dlg:
                with ui.column().classes("w-[400px] gap-4"):
                    ui.label("Разделение паллеты").classes("text-xl font-bold text-orange-400")
                    src_pallet_id = ui.number().classes("hidden")
                    src_label = ui.label().classes("text-gray-300 font-mono")
                    max_qty = ui.number().classes("hidden")
                    split_qty = (
                        ui.number("Отделить количество", min=1)
                        .classes("w-full")
                        .props("dark standout rounded")
                    )

                    async def execute_split():
                        if not split_qty.value or split_qty.value >= max_qty.value:
                            NotifyHelper.warning(
                                "Некорректное количество (должно быть меньше остатка)"
                            )
                            return
                        async with self.scope() as req:
                            system = await req.get(ProductionSystem)
                            system.split_production_unit(
                                int(src_pallet_id.value), int(split_qty.value), self.user
                            )
                        split_dlg.close()
                        await self.refresh_grid()
                        NotifyHelper.warning("Паллета успешно разделена")

                    ui.button("ОТДЕЛИТЬ В НОВУЮ ПАЛЛЕТУ", on_click=execute_split).classes(
                        "w-full h-12 bg-orange-600 text-white rounded-xl shadow-lg"
                    )

            self.grid.on(
                "split",
                lambda e: (
                    src_pallet_id.set_value(e.args["id"]),
                    src_label.set_text(
                        f"Паллета: {e.args['label_id']} (Доступно: {e.args['qty_produced']})"
                    ),
                    max_qty.set_value(e.args["qty_produced"]),
                    split_qty.set_value(1),
                    split_qty.props(f"max={e.args['qty_produced'] - 1}"),
                    split_dlg.open(),
                ),
            )

            # Merge Actions
            with ui.row().classes("w-full justify-between items-center mt-4"):
                ui.label("Слияние (Merge) доступно при выборе нескольких паллет.").classes(
                    "text-gray-400 text-sm"
                )

                async def execute_merge():
                    selected = self.grid.selected
                    if len(selected) < 2:
                        NotifyHelper.success("Выберите минимум 2 паллеты (галочками) для слияния")
                        return
                    # Pick the first selected as the target, merge the rest into it
                    target_id = selected[0]["id"]
                    source_ids = [s["id"] for s in selected[1:]]
                    async with self.scope() as req:
                        system = await req.get(ProductionSystem)
                        system.merge_production_units(source_ids, target_id, self.user)
                    self.grid.selected.clear()
                    await self.refresh_grid()
                    NotifyHelper.info(f"Паллеты слиты в {selected[0]['label_id']}")

                ui.button("СЛИТЬ В ПЕРВУЮ ВЫБРАННУЮ")

            # Load data on open
            ui.timer(0.1, self.refresh_grid, once=True)

    async def handle_shipment(self, pallet_row):
        """Handle pallet shipment."""
        try:
            async with self.scope() as req:
                system = await req.get(ProductionSystem)
                system.mark_as_shipped(pallet_row["id"], self.user)
            NotifyHelper.success(f"Паллета {pallet_row['label_id']} отгружена")
            await self.refresh_grid()
        except Exception as e:
            NotifyHelper.info(f"Ошибка отгрузки: {e}")

    async def refresh_grid(self):
        """Update grid data."""
        async with self.scope() as req:
            system = await req.get(ProductionSystem)
            if self.search_term.value and len(self.search_term.value) >= 2:
                stmt = (
                    select(ProductionUnit)
                    .where(ProductionUnit.label_id.contains(self.search_term.value))  # type: ignore[attr-defined]
                    .order_by(ProductionUnit.id.desc())  # type: ignore[attr-defined]
                )
                units = system.db_session.exec(stmt).all()
            else:
                units = system.get_recent_production_units()

            self.grid.rows[:] = [
                {
                    "id": u.id,
                    "label_id": u.label_id,
                    "qty_produced": u.qty_produced,
                    "parent_label_id": u.parent_label_id or "-",
                    "created_by": u.created_by,
                    "status_label": "НА СКЛАДЕ" if u.is_stock else "ОТГРУЖЕНО",
                    "status_color": "emerald" if u.is_stock else "slate-500",
                    "can_ship": u.is_stock,
                }
                for u in units
            ]
            self.grid.update()
