from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import Consumable
from docuflow.features.consumables.system import ConsumableSystem
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper


def register_consumables_view():
    ViewRegistry.register(
        ViewInfo(
            name="consumables",
            label="Consumables",
            icon="inventory",
            render_fn=consumables_view_wrapper,
            dependencies=[ConsumableSystem],
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def consumables_view_wrapper(
    system: ConsumableSystem, system_scope: Any, layout: Any, **kwargs
):
    """Wrapper to instantiate and render the ConsumableView."""
    view = ConsumableView(system, system_scope, layout=layout)
    await view.render()


class ConsumableView(BaseDocuWidget):
    """
    Workshop supply and consumable dashboard.
    """

    def __init__(self, system: ConsumableSystem, system_scope: Any, layout: Any = None):
        super().__init__(system_scope)
        self.system = system
        self.layout = layout
        self.table: Any = None
        self.log_container: Any = None
        self.active_consumable: Consumable | None = None

    async def render(self):
        """Render the consumables management dashboard."""
        with ui.column().classes("w-full gap-6 p-4"):
            # --- Header ---
            with ui.row().classes("w-full justify-between items-end border-b border-zinc-800 pb-4"):
                with ui.column().classes("gap-1"):
                    ui.label("Учёт расходных материалов").classes(
                        "text-2xl font-bold text-zinc-100"
                    )
                    ui.label("Мониторинг сопел, линз и вспомогательных материалов").classes(
                        "text-sm text-zinc-400"
                    )

                with ui.row().classes("gap-4"):
                    ui.button("Добавить SKU", icon="add", on_click=self.create_dialog).props(
                        "flat color=primary"
                    )
                    ui.button(icon="refresh", on_click=self.refresh_all).props("flat")

            # --- Main Content Layout ---
            with ui.row().classes("w-full gap-6 items-start"):
                # Left: Main Status Table
                with ui.column().classes("flex-grow gap-4"):
                    await self._render_status_table()

                # Right: Audit Log Side-panel
                with ui.column().classes("w-80 gap-4"):
                    ui.label("История движений").classes(
                        "text-xs font-bold uppercase text-zinc-500 tracking-widest"
                    )
                    self.log_container = ui.column().classes(
                        "w-full gap-2 border-l border-zinc-900 pl-4"
                    )
                    await self.refresh_logs()

    async def _render_status_table(self):
        """Build the main supply status table."""
        columns = [
            {"name": "status", "label": "", "field": "status", "align": "left"},
            {
                "name": "name",
                "label": "Наименование",
                "field": "name",
                "required": True,
                "align": "left",
            },
            {"name": "category", "label": "Категория", "field": "category", "align": "left"},
            {"name": "quantity", "label": "Остаток", "field": "quantity", "align": "center"},
            {
                "name": "min_quantity",
                "label": "Мин. запас",
                "field": "min_quantity",
                "align": "center",
            },
            {"name": "actions", "label": "Действия", "field": "actions", "align": "right"},
        ]

        self.table = ui.table(columns=columns, rows=[], row_key="id").classes(
            "w-full bg-zinc-900 border-zinc-800 text-zinc-200 shadow-xl"
        )

        # Custom cell formatting via props/slots (NiceGUI style)
        self.table.add_slot(
            "body-cell-status",
            """
            <q-td :props="props">
                <q-icon v-if="props.row.quantity <= props.row.min_quantity" name="warning" color="red" size="xs" />
                <q-icon v-else name="check_circle" color="emerald" size="xs" />
            </q-td>
        """,
        )

        self.table.add_slot(
            "body-cell-name",
            """
            <q-td :props="props" :class="props.row.quantity <= props.row.min_quantity ? 'text-red-500 font-bold' : ''">
                {{ props.value }}
                <div class="text-[10px] text-zinc-500 uppercase">{{ props.row.unit }}</div>
            </q-td>
        """,
        )

        self.table.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
                <q-btn-group flat>
                    <q-btn flat icon="remove" color="red-4" @click="$parent.$emit('use', props.row)" />
                    <q-btn flat icon="add" color="emerald-4" @click="$parent.$emit('restock', props.row)" />
                    <q-btn flat icon="history" @click="$parent.$emit('history', props.row)" />
                </q-btn-group>
            </q-td>
        """,
        )

        self.table.on("use", lambda msg: self.open_op_dialog(msg.args, "use"))
        self.table.on("restock", lambda msg: self.open_op_dialog(msg.args, "restock"))
        self.table.on("history", lambda msg: self.refresh_logs(msg.args["id"]))

        await self.refresh_table()

    async def refresh_table(self):
        """Update table data."""
        async with self.scope() as req:
            system = await req.get(ConsumableSystem)
            consumables = system.list_consumables()

        self.table.rows = [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "quantity": c.quantity,
                "min_quantity": c.min_quantity,
                "unit": c.unit,
            }
            for c in consumables
        ]

    async def refresh_logs(self, consumable_id: int | None = None):
        """Reload the log panel."""
        if not self.log_container:
            return
        self.log_container.clear()

        # If no specific ID, show last 20 total or header
        if not consumable_id:
            with self.log_container:
                ui.label("Выберите материал для просмотра истории").classes(
                    "text-xs text-zinc-600 italic mt-8"
                )
            return

        async with self.scope() as req:
            system = await req.get(ConsumableSystem)
            logs = system.get_log(consumable_id, limit=20)

        if not logs:
            with self.log_container:
                ui.label("Истории нет").classes("text-xs text-zinc-600 italic mt-4")
            return

        with self.log_container:
            for log in logs:
                color = (
                    "emerald-500"
                    if log.operation == "restock"
                    else "red-500"
                    if log.operation in ["use", "write_off"]
                    else "blue-500"
                )
                with ui.card().classes(
                    f"w-full bg-zinc-900/50 border-l-2 border-{color} p-2 gap-0 shadow-none"
                ):
                    with ui.row().classes("w-full justify-between items-start"):
                        ui.label(log.operation.upper()).classes(
                            f"text-[9px] font-bold text-{color}"
                        )
                        ui.label(log.created_at.strftime("%H:%M")).classes(
                            "text-[9px] text-zinc-600"
                        )

                    ui.label(f"{'+' if log.qty_delta > 0 else ''}{log.qty_delta:.1f}").classes(
                        "text-lg font-mono text-zinc-200 mt-1"
                    )
                    if log.note:
                        ui.label(log.note).classes("text-[10px] text-zinc-500 mt-1 italic")
                    ui.label(f"От: {log.author}").classes(
                        "text-[8px] text-zinc-700 text-right w-full"
                    )

    def open_op_dialog(self, row: dict, op_type: str):
        """Dialog for adding/removing stock."""
        title = "Расход (Использование)" if op_type == "use" else "Поступление (Пополнение)"
        icon = "remove" if op_type == "use" else "add"
        color = "red" if op_type == "use" else "emerald"

        with ui.dialog() as d, ui.card().classes("bg-zinc-900 border border-zinc-800 w-80"):
            with ui.row().classes("items-center gap-2 mb-4"):
                ui.icon(icon, color=color, size="24px")
                ui.label(title).classes("text-lg font-bold text-zinc-100")

            ui.label(f"Материал: {row['name']}").classes("text-sm text-zinc-400 mb-4")

            qty = ui.number(
                label="Количество", placeholder=f"ед. ({row['unit']})", format="%.2f"
            ).classes("w-full")
            note = ui.input(label="Примечание (Задание / Номер заказа)").classes("w-full")

            async def submit():
                if qty.value is None or qty.value <= 0:
                    return
                async with self.scope() as req:
                    system = await req.get(ConsumableSystem)
                    if op_type == "use":
                        system.use(row["id"], qty.value, user="operator", note=note.value)
                    else:
                        system.restock(row["id"], qty.value, user="operator", note=note.value)

                d.close()
                await self.refresh_all()
                NotifyHelper.info("Операция выполнена")

            with ui.row().classes("w-full justify-end mt-4"):
                ui.button("Отмена", on_click=d.close).props("flat color=zinc-500")
                ui.button("ОК", on_click=submit).props(f"flat color={color}")

        d.open()

    def create_dialog(self):
        """Dialog to create a new catalog item."""
        with ui.dialog() as d, ui.card().classes("bg-zinc-900 border border-zinc-800 w-96"):
            ui.label("Новая позиция каталога").classes("text-lg font-bold text-zinc-100 mb-4")

            name = ui.input(label="Наименование", placeholder="Напр: Сопло 1.5мм").classes("w-full")
            cat = ui.select(
                ["nozzle", "lens", "shield", "gas", "tape", "filter", "other"],
                label="Категория",
                value="nozzle",
            ).classes("w-full")
            unit = ui.select(
                ["pcs", "kg", "m", "pack", "liter"], label="Ед. изм.", value="pcs"
            ).classes("w-full")
            min_q = ui.number(label="Мин. критический остаток", value=5).classes("w-full")

            async def submit():
                if not name.value:
                    return
                async with self.scope() as req:
                    system = await req.get(ConsumableSystem)
                    system.create_consumable(name.value, cat.value, unit.value, min_q.value)
                d.close()
                await self.refresh_all()
                NotifyHelper.info("Новая позиция добавлена")

            with ui.row().classes("w-full justify-end mt-6"):
                ui.button("Отмена", on_click=d.close).props("flat")
                ui.button("Создать", on_click=submit).props("flat color=primary")
        d.open()

    async def refresh_all(self):
        await self.refresh_table()
        # Full refresh of logs is tricky without last ID, so we just clear sidebar header
        if self.log_container:
            self.log_container.clear()
            with self.log_container:
                ui.label("Выберите материал для просмотра истории").classes(
                    "text-xs text-zinc-600 italic mt-8"
                )
