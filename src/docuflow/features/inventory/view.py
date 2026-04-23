from typing import Any

from nicegui import ui

from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.inventory.system import InventorySystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.styles import Styles as S
from docuflow.lib.widgets.ui_utils import NotifyHelper


def register_warehouse_view():
    """Register the warehouse view in the global registry."""
    ViewRegistry.register(
        ViewInfo(
            name="warehouse",
            label="Warehouse",
            icon="inventory_2",
            render_fn=warehouse_view_wrapper,
            dependencies=[InventorySystem],
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def warehouse_view_wrapper(inventory_system: InventorySystem, system_scope: Any, layout: Any):
    """Wrapper to instantiate and render the WarehouseView."""
    view = WarehouseView(inventory_system, system_scope, layout)
    await view.render()


class WarehouseView(BaseDocuWidget):
    """Provides the decentralized material stock management grid."""

    def __init__(self, inventory_system: InventorySystem, system_scope: Any, layout: Any):
        super().__init__(system_scope)
        self.inventory_system = inventory_system
        self.layout = layout

    async def render(self):
        """Render the warehouse UI."""
        with ui.column().classes(S.PAGE):
            ui.label("Склад и Материалы").classes(S.HEADING_LARGE)

            with ui.tabs().classes("w-full text-indigo-400") as tabs:
                catalog_tab = ui.tab("КАТАЛОГ")
                stock_tab = ui.tab("ОСТАТКИ")
                supply_tab = ui.tab("ОЧЕРЕДЬ ПОДАЧИ")
                audit_tab = ui.tab("ИСТОРИЯ")

            with ui.tab_panels(tabs, value=catalog_tab).classes("w-full bg-transparent"):
                # --- TAB: SUPPLY QUEUE (Live Requests) ---
                with ui.tab_panel(supply_tab):

                    @ui.refreshable
                    async def render_supply_requests():
                        async with self.scope() as req:
                            fresh_system = await req.get(InventorySystem)
                            requests = fresh_system.get_active_supply_requests()

                        if not requests:
                            with ui.card().classes(f"w-full p-8 text-center {S.CARD_DARK}"):
                                ui.icon("check_circle", color="emerald").classes("text-6xl mb-4")
                                ui.label("Все накормлены. Активных запросов нет.").classes(
                                    "text-xl text-slate-400"
                                )
                        else:
                            with ui.grid(columns=3).classes(f"w-full {S.GAP_4}"):
                                for req_log in requests:
                                    with ui.card().classes(
                                        f"{S.CARD_DARK} p-4 border-l-4 border-orange-500"
                                    ):
                                        with ui.row().classes(f"{S.ROW} w-full {S.MB_2}"):
                                            ui.label(req_log.created_at.strftime("%H:%M")).classes(
                                                "text-xs text-indigo-300"
                                            )
                                            ui.badge("СРОЧНО").props("color=orange")

                                        raw = req_log.message
                                        msg = raw.replace("[LOGISTICS_REQUEST]", "").strip()
                                        ui.label(msg).classes(
                                            f"{S.BODY} font-bold text-white {S.MB_4}"
                                        )

                                        with ui.row().classes("w-full justify-end"):
                                            def _fulfill(r=req_log):
                                                self.handle_supply_fulfillment(
                                                    r, render_supply_requests
                                                )

                                            ui.button("ПОДАНО", on_click=_fulfill).classes(
                                                "bg-emerald-600 text-white rounded-lg"
                                            )

                        # Safe self-perpetuating refresh tied to Layout lifecycle
                        self.layout.register_timer(
                            ui.timer(15.0, render_supply_requests.refresh, once=True)
                        )

                    await render_supply_requests()

                # --- TAB: CATALOG (Material Types) ---
                with ui.tab_panel(catalog_tab):

                    async def refresh_catalog():
                        # H2 FIX: Fresh session for background/late refresh
                        async with self.scope() as req:
                            fresh_system = await req.get(InventorySystem)
                            types = fresh_system.get_material_catalog()
                            catalog_grid.rows[:] = [t.model_dump() for t in types]
                            catalog_grid.update()

                    catalog_cols = [
                        {
                            "name": "code",
                            "label": "Код (Марка)",
                            "field": "code",
                            "align": "left",
                            "sortable": True,
                        },
                        {
                            "name": "thickness",
                            "label": "Толщина (мм)",
                            "field": "thickness",
                            "align": "center",
                        },
                        {
                            "name": "form_factor",
                            "label": "Тип",
                            "field": "form_factor",
                            "align": "center",
                        },
                        {
                            "name": "cut_speed",
                            "label": "V-рез (мм/м)",
                            "field": "cut_speed_mm_per_min",
                        },
                        {
                            "name": "drift",
                            "label": "Drift%",
                            "field": "time_tolerance_pct",
                            "align": "center",
                        },
                        {"name": "actions", "label": "", "field": "id", "align": "right"},
                    ]

                    catalog_grid = ui.table(columns=catalog_cols, rows=[], row_key="id").classes(
                        "w-full glass-card text-white"
                    )
                    catalog_grid.add_slot(
                        "body-cell-drift",
                        """
                        <q-td :props="props">
                            <q-badge :color="props.value < 10 ? 'emerald' : (props.value < 25 ? 'orange' : 'red')">
                                {{ props.value }}%
                            </q-badge>
                        </q-td>
                        """,
                    )
                    catalog_grid.add_slot(
                        "body-cell-actions",
                        """
                        <q-td :props="props">
                            <q-btn flat round dense color="indigo" icon="settings" @click="$parent.$emit('settings', props.row)" />
                            <q-btn flat round dense color="orange" icon="shopping_cart" @click="$parent.$emit('reorder', props.row)" />
                        </q-td>
                    """,
                    )

                    # --- Catalog Settings Dialog ---
                    with ui.dialog().classes("glass-card p-6") as settings_dialog:
                        with ui.column().classes("w-[500px] gap-4"):
                            ui.label("Настройки материала").classes(
                                "text-xl font-bold text-indigo-400"
                            )
                            with ui.row().classes("w-full gap-4"):
                                v_cut = (
                                    ui.number("V резки (мм/мин)", value=3000)
                                    .classes("flex-1")
                                    .props("dark standout rounded")
                                )
                                t_pierce = (
                                    ui.number("T прокола (сек)", value=3.0)
                                    .classes("flex-1")
                                    .props("dark standout rounded")
                                )
                            with ui.row().classes("w-full gap-4"):
                                v_idle = (
                                    ui.number("V холост. (мм/мин)", value=10000)
                                    .classes("flex-1")
                                    .props("dark standout rounded")
                                )
                                drift_limit = (
                                    ui.number("Drift Limit %", value=InventorySystem.DEFAULT_TIME_TOLERANCE_PCT)
                                    .classes("flex-1")
                                    .props("dark standout rounded")
                                )

                            target_id = ui.number().classes("hidden")  # Hidden state

                            async def save_settings():
                                # H2 FIX: Fresh session for DB update
                                async with self.scope() as req:
                                    fresh_system = await req.get(InventorySystem)
                                    updated = fresh_system.update_material_settings(
                                        target_id.value,
                                        cut_speed_mm_per_min=v_cut.value,
                                        pierce_time_sec=t_pierce.value,
                                        idle_speed_mm_per_min=v_idle.value,
                                        time_tolerance_pct=drift_limit.value,
                                    )
                                    if updated:
                                        settings_dialog.close()
                                        await refresh_catalog()
                                        NotifyHelper.warning("Параметры обновлены")

                            ui.button("Сохранить", on_click=save_settings).classes(
                                "w-full h-12 vibrant-btn text-white rounded-xl shadow-lg"
                            )

                    catalog_grid.on(
                        "settings",
                        lambda e: (
                            target_id.set_value(e.args["id"]),
                            v_cut.set_value(e.args["cut_speed_mm_per_min"]),
                            t_pierce.set_value(e.args["pierce_time_sec"]),
                            v_idle.set_value(e.args["idle_speed_mm_per_min"]),
                            drift_limit.set_value(e.args["time_tolerance_pct"]),
                            settings_dialog.open(),
                        ),
                    )

                    # --- Reorder Dialog ---
                    with ui.dialog().classes("glass-card p-6") as reorder_dialog:
                        with ui.column().classes("w-[400px] gap-4"):
                            ui.label("Сформировать заказ").classes(
                                "text-xl font-bold text-orange-400"
                            )
                            reorder_qty = (
                                ui.number("Количество листов", value=10)
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            reorder_note = (
                                ui.textarea("Примечание")
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            reorder_mat_id = ui.number().classes("hidden")

                            async def submit_reorder():
                                async with self.scope() as req:
                                    fresh_system = await req.get(InventorySystem)
                                    fresh_system.request_material_reorder(
                                        reorder_mat_id.value,
                                        reorder_qty.value,
                                        str(reorder_note.value),
                                        author="system",
                                    )
                                reorder_dialog.close()
                                NotifyHelper.warning("Заказ отправлен в чат!")

                            ui.button("ОТПРАВИТЬ", on_click=submit_reorder).classes(
                                "w-full h-12 bg-orange-600 text-white rounded-xl shadow-lg"
                            )

                    catalog_grid.on(
                        "reorder",
                        lambda e: (reorder_mat_id.set_value(e.args["id"]), reorder_dialog.open()),
                    )

                    ui.timer(0.1, refresh_catalog, once=True)

                    # --- Create Material Dialog ---
                    with ui.dialog().classes("glass-card p-6") as create_mat_dialog:
                        with ui.column().classes("w-[500px] gap-4"):
                            ui.label("Регистрация Материала").classes(
                                "text-xl font-bold text-emerald-400"
                            )
                            mat_code = (
                                ui.input("Код/Название (напр. ALU 3.0)")
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            mat_thk = (
                                ui.number("Толщина (мм)", value=1.0)
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            mat_unit = (
                                ui.select(["pcs", "kg", "m2"], label="Ед. изм.", value="pcs")
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            mat_type = (
                                ui.select(
                                    ["SHEET", "TUBE", "BAR", "OTHER"],
                                    label="Форм-фактор",
                                    value="SHEET",
                                )
                                .classes("w-full")
                                .props("dark standout rounded")
                            )

                            async def handle_create_mat():
                                if mat_code.value and mat_thk.value:
                                    async with self.scope() as req:
                                        fresh_system = await req.get(InventorySystem)
                                        fresh_system.create_material_definition(
                                            code=mat_code.value,
                                            thickness=mat_thk.value,
                                            primary_unit=mat_unit.value,
                                            form_factor=mat_type.value,
                                            # Default time params
                                            cut_speed_mm_per_min=3000,
                                            pierce_time_sec=3.0,
                                            idle_speed_mm_per_min=10000,
                                            time_tolerance_pct=InventorySystem.DEFAULT_TIME_TOLERANCE_PCT,
                                        )
                                    create_mat_dialog.close()
                                    await refresh_catalog()
                                    NotifyHelper.warning(
                                        f"Материал {mat_code.value} добавлен")

                            ui.button("ЗАРЕГИСТРИРОВАТЬ", on_click=handle_create_mat).classes(
                                "w-full h-12 vibrant-btn text-white rounded-xl shadow-lg"
                            )

                    with ui.row().classes("w-full justify-end mt-4"):
                        ui.button(
                            "НОВЫЙ МАТЕРИАЛ", icon="add", on_click=create_mat_dialog.open
                        ).classes("vibrant-btn text-white rounded-xl h-12 px-6")

                # --- TAB: STOCK (Batches) ---
                with ui.tab_panel(stock_tab):

                    async def refresh_stock():
                        async with self.scope() as req:
                            fresh_system = await req.get(InventorySystem)
                            batches = fresh_system.get_all_stock()
                            stock_grid.rows[:] = [
                                {
                                    **b.model_dump(),
                                    "mat_code": b.material_type.code if b.material_type else "UNK",
                                }
                                for b in batches
                            ]
                            stock_grid.update()

                    stock_cols = [
                        {
                            "name": "mat_code",
                            "label": "Материал",
                            "field": "mat_code",
                            "align": "left",
                        },
                        {
                            "name": "batch_code",
                            "label": "Партия",
                            "field": "batch_code",
                            "align": "center",
                        },
                        {
                            "name": "quantity",
                            "label": "Остаток",
                            "field": "quantity",
                            "sortable": True,
                        },
                        {
                            "name": "location",
                            "label": "Место",
                            "field": "location",
                            "align": "center",
                        },
                        {"name": "status", "label": "Статус", "field": "status", "align": "center"},
                        {"name": "actions", "label": "", "field": "id", "align": "right"},
                    ]

                    stock_grid = ui.table(columns=stock_cols, rows=[], row_key="id").classes(
                        "w-full glass-card text-white"
                    )
                    stock_grid.add_slot(
                        "body-cell-actions",
                        """
                        <q-td :props="props">
                            <q-btn flat round dense color="green" icon="exposure_plus_1" @click="$parent.$emit('correct', props.row)" />
                        </q-td>
                    """,
                    )

                    # --- Income/Receive Dialog ---
                    with ui.dialog().classes("glass-card p-6") as income_dialog:
                        with ui.column().classes("w-[400px] gap-4"):
                            ui.label("Приход материала").classes("text-xl font-bold text-green-400")

                            # Load catalog for selector
                            async with self.scope() as req:
                                fresh_system = await req.get(InventorySystem)
                                catalog_opts = {
                                    m.id: m.code for m in fresh_system.get_material_catalog()
                                }

                            mat_selector = (
                                ui.select(
                                    catalog_opts,
                                    label="Выбрать марку",
                                )
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            qty_income = (
                                ui.number("Кол-во", value=1.0)
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            batch_input = (
                                ui.input("Код партии")
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            loc_input = (
                                ui.input("Место хранения", value="MAIN")
                                .classes("w-full")
                                .props("dark standout rounded")
                            )

                            async def handle_income():
                                async with self.scope() as req:
                                    fresh_system = await req.get(InventorySystem)
                                    fresh_system.receive_material_batch(
                                        mat_selector.value,
                                        qty_income.value,
                                        batch_input.value,
                                        loc_input.value,
                                    )
                                income_dialog.close()
                                await refresh_stock()
                                NotifyHelper.warning("Склад обновлён")

                            ui.button("ПРИНЯТЬ", on_click=handle_income).classes(
                                "w-full h-12 bg-green-700 text-white rounded-xl shadow-lg"
                            )

                    # --- Correction Dialog ---
                    with ui.dialog().classes("glass-card p-6") as correct_dialog:
                        with ui.column().classes("w-[400px] gap-4"):
                            ui.label("Инвентаризация").classes("text-xl font-bold text-yellow-400")
                            actual_qty = (
                                ui.number("Фактический остаток")
                                .classes("w-full")
                                .props("dark standout rounded")
                            )
                            corr_reason = (
                                ui.input("Причина").classes("w-full").props("dark standout rounded")
                            )
                            corr_stock_id = ui.number().classes("hidden")

                            async def apply_correction():
                                async with self.scope() as req:
                                    fresh_system = await req.get(InventorySystem)
                                    fresh_system.record_inventory_correction(
                                        corr_stock_id.value,
                                        actual_qty.value,
                                        corr_reason.value,
                                        author="system",
                                    )
                                correct_dialog.close()
                                await refresh_stock()
                                NotifyHelper.success("Инвентаризация проведена")

                            ui.button("КОРРЕКТИРОВАТЬ", on_click=apply_correction).classes(
                                "w-full h-12 bg-yellow-600 text-white rounded-xl shadow-lg"
                            )

                    stock_grid.on(
                        "correct",
                        lambda e: (
                            corr_stock_id.set_value(e.args["id"]),
                            actual_qty.set_value(e.args["quantity"]),
                            correct_dialog.open(),
                        ),
                    )

                    with ui.row().classes("w-full justify-end"):
                        ui.button("ПРИНЯТЬ ЛИСТЫ")

                    ui.timer(0.1, refresh_stock, once=True)

                # --- TAB: AUDIT (History) ---
                with ui.tab_panel(audit_tab):

                    async def refresh_audit():
                        async with self.scope() as req:
                            fresh_system = await req.get(InventorySystem)
                            logs = fresh_system.get_audit_history(limit=100)
                            audit_grid.rows[:] = [log.model_dump() for log in logs]
                            audit_grid.update()

                    audit_cols = [
                        {
                            "name": "created_at",
                            "label": "Дата/Время",
                            "field": "created_at",
                            "align": "left",
                        },
                        {"name": "operation", "label": "Оп.", "field": "operation", "align": "center"},
                        {
                            "name": "qty_delta",
                            "label": "Дельта",
                            "field": "qty_delta",
                            "align": "center",
                        },
                        {
                            "name": "reason",
                            "label": "Причина/Детали",
                            "field": "reason",
                            "align": "left",
                        },
                        {"name": "author", "label": "Автор", "field": "author"},
                        {"name": "node_id", "label": "Узел", "field": "node_id"},
                    ]
                    audit_grid = ui.table(columns=audit_cols, rows=[], row_key="id").classes(
                        "w-full glass-card text-white"
                    )

                    ui.timer(0.1, refresh_audit, once=True)

    async def handle_supply_fulfillment(self, request_log, refresh_fn):
        """Handle fulfillment of a supply request."""
        try:
            # H2 FIX: Always resolve a fresh system for actions to avoid DetachedInstanceError
            async with self.scope() as req:
                fresh_system = await req.get(InventorySystem)
                fresh_system.resolve_supply_request(request_log.id, "warehouse_op")
            NotifyHelper.info(f"Запрос {request_log.id} выполнен")
            refresh_fn.refresh()
        except Exception as e:
            NotifyHelper.info(f"Ошибка выполнения запроса: {e}")
