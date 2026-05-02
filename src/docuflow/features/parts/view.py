from functools import partial
from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import (
    PartLibrary,
    PartTemplate,
    ProductionUnit,
    WorkItem,
)
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.parts.order_cart import OrderCart
from docuflow.features.parts.rework_generator import ReworkGenerator
from docuflow.features.parts.system import PartLibrarySystem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.order_cart_panel import OrderCartPanel
from docuflow.lib.widgets.part_preview import PartPreview
from docuflow.lib.widgets.ui_utils import NotifyHelper


def register_parts_view() -> None:
    ViewRegistry.register(
        ViewInfo(
            name="parts",
            label="Parts",
            icon="extension",
            render_fn=parts_view_wrapper,
            dependencies=[PartLibrarySystem],
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def parts_view_wrapper(
    parts_system: PartLibrarySystem, system_scope: Any, layout: Any, **kwargs: Any
) -> None:
    """Wrapper to instantiate and render the PartLibraryView."""
    view: PartLibraryView = PartLibraryView(parts_system, system_scope, layout=layout)
    await view.render()  # type: ignore[call-arg]


class PartLibraryView(BaseDocuWidget):
    """
    Electronic catalog of all unique parts scanned by the system.
    """

    def __init__(
        self, parts_system: PartLibrarySystem, system_scope: Any, layout: Any = None
    ) -> None:
        super().__init__(system_scope)
        self.parts_system = parts_system
        self.layout = layout
        self.grid: Any = None
        self.search_query = ""
        self.mat_filter: Any = None
        self.bbox_x_min = 0
        self.bbox_x_max = 2000
        self.cart = OrderCart()
        self.cart_panel = OrderCartPanel(
            self.cart,
            on_create_order=self._create_rework_order,
            system_scope=system_scope,
        )

    @ui.refreshable
    async def render(self) -> None:
        """Render the part library dashboard."""
        with ui.column().classes("w-full gap-6 p-4"):
            # --- Header & Filters ---
            with ui.row().classes("w-full justify-between items-end border-b border-zinc-800 pb-4"):
                with ui.column().classes("gap-1"):
                    ui.label("Справочник деталей").classes("text-2xl font-bold text-zinc-100")
                    ui.label("Реестр уникальных SKU с историей использования").classes(
                        "text-sm text-zinc-400"
                    )

                with ui.row().classes("gap-4 items-center"):
                    ui.input(
                        placeholder="Поиск по SKU...",
                        on_change=self.render.refresh,  # type: ignore[attr-defined]
                    ).bind_value(self, "search_query").classes("w-64 bg-zinc-900 border-zinc-800")

                    ui.button("Гео-поиск", icon="straighten", on_click=self.open_geo_search).props(
                        "flat color=primary"
                    )

                    ui.button(icon="refresh", on_click=self.render.refresh).props("flat")  # type: ignore[attr-defined]

            # --- Order Cart Panel ---
            cart_panel: OrderCartPanel = self.cart_panel
            cart_panel.render()  # type: ignore[call-arg]

            # --- Main Content (Grid) ---
            self.grid: Any = ui.grid(columns=6).classes("w-full gap-4")
            await self._build_parts_grid()

            # Auto-refresh every 15 seconds
            if self.layout:
                self.layout.register_timer(ui.timer(15.0, self.render.refresh, once=True))
            else:
                ui.timer(15.0, self.render.refresh, once=True)

    async def _build_parts_grid(self) -> None:
        """Internal helper to build the grid content."""
        async with self.scope() as req:
            parts_system: PartLibrarySystem = await req.get(PartLibrarySystem)
            parts: list[PartLibrary] = parts_system.search_part_library(
                sku_filter=self.search_query if len(self.search_query) >= 2 else None, limit=50
            )
            # Eagerly load attributes while session is active
            part_data: list[dict[str, Any]] = [
                {
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "svg_preview_path": p.svg_preview_path,
                    "bbox_x": p.bbox_x,
                    "bbox_y": p.bbox_y,
                }
                for p in (parts or [])
            ]

        if not part_data:
            with self.grid:
                ui.label("Детали не найдены").classes(
                    "col-span-full text-center text-zinc-600 mt-12 py-8 "
                    "border-2 border-dashed border-zinc-800 rounded-lg"
                )
            return

        with self.grid:
            for pd in part_data:
                with (
                    ui.card()
                    .classes(
                        "group relative overflow-hidden bg-zinc-900 "
                        "border-zinc-800 hover:border-blue-500/50 transition-all cursor-pointer p-3"
                    )
                    .on("click", lambda *args, pid=pd["id"]: self.open_part_details(pid))
                ):
                    # SVG Thumbnail
                    PartPreview(pd["svg_preview_path"]).render()

                    # SKU & Metrics
                    with ui.column().classes("mt-2 gap-0"):
                        ui.label(pd["sku"]).classes(
                            "text-xs font-bold truncate text-zinc-200 group-hover:text-blue-400"
                        )
                        ui.label(f"{pd['bbox_x']:.1f} × {pd['bbox_y']:.1f} мм").classes(
                            "text-[10px] text-zinc-500 uppercase tracking-tighter"
                        )

                    # Hover Overlay
                    with ui.row().classes(
                        "absolute top-2 right-2 opacity-0 "
                        "group-hover:opacity-100 transition-opacity"
                    ):
                        ui.icon("info", size="16px").classes("text-blue-500")
                        cart_btn: Any = ui.button(
                            icon="add_shopping_cart",
                            on_click=partial(self._add_to_cart, pd["sku"], pd.get("name")),
                        ).props("flat dense round size=xs color=green")
                        cart_btn.on("click", js_handler="(e) => e.stopPropagation()")

    def _add_to_cart(self, sku: str, name: str | None = None) -> None:
        self.cart.add(sku, name=name or sku, qty=1)
        self.cart_panel.render.refresh()
        NotifyHelper.success(f"Добавлено: {sku}")

    async def _create_rework_order(self, name: str, items: list) -> None:
        async with self.scope() as req:
            tb_system: TaskBoardSystem = await req.get(TaskBoardSystem)
            project: Any = tb_system.resolve_default_workshop_project()
            parts_system: PartLibrarySystem = await req.get(PartLibrarySystem)
            gen: ReworkGenerator = ReworkGenerator(
                parts_system.db_session, parts_system.config.shared_path
            )
            gen.generate(name, project.id, items)
        NotifyHelper.success(f"Заказ {name} создан")
        self.render.refresh()

    async def open_part_details(self, part_id: int) -> None:
        """Open detailed modal for a specific part."""
        # Reload part data from a fresh session to avoid detached instance errors
        async with self.scope() as req:
            from docuflow.features.parts.system import PartLibrarySystem

            p_sys: PartLibrarySystem = await req.get(PartLibrarySystem)
            fresh: PartLibrary | None = p_sys.get_part(part_id)
            if fresh:
                pd: dict[str, Any] = {
                    "sku": fresh.sku,
                    "svg_preview_path": fresh.svg_preview_path,
                    "version": fresh.version,
                    "first_seen_at": fresh.first_seen_at,
                    "bbox_x": fresh.bbox_x,
                    "bbox_y": fresh.bbox_y,
                    "contour_count": fresh.contour_count,
                    "hole_count": fresh.hole_count,
                    "corner_count": fresh.corner_count,
                }
            else:
                NotifyHelper.error("Деталь не найдена в БД")
                return

        with (
            ui.dialog() as dialog,
            ui.card().classes(
                "w-[900px] max-w-none bg-zinc-950 p-0 overflow-hidden border border-zinc-800"
            ),
        ):
            # Header
            with ui.row().classes(
                "w-full bg-zinc-900 border-b border-zinc-800 p-4 justify-between items-center"
            ):
                with ui.column().classes("gap-0"):
                    ui.label(pd["sku"]).classes("text-xl font-bold text-zinc-100")
                    first_seen_str: str = (
                        pd["first_seen_at"].strftime("%d.%m.%Y") if pd["first_seen_at"] else "—"
                    )
                    version_label: str = (
                        f"Версия {pd['version']} • Впервые замечена: {first_seen_str}"
                    )
                    ui.label(version_label).classes("text-xs text-zinc-500")
                ui.button(icon="close", on_click=dialog.close).props("flat color=white")

            with ui.row().classes("w-full p-6 gap-8"):
                # Left: Large Preview & Stats
                with ui.column().classes("w-1/3 gap-4"):
                    PartPreview(pd["svg_preview_path"], size="280px").render()

                    with ui.card().classes("w-full bg-zinc-900/50 border-zinc-800 p-4"):
                        ui.label("Метрики").classes(
                            "text-xs font-bold uppercase text-zinc-500 mb-2"
                        )
                        self._stat_row(
                            "Габариты",
                            f"{pd['bbox_x']:.1f} × {pd['bbox_y']:.1f} мм",
                        )
                        self._stat_row("Контуров", str(pd["contour_count"] or 0))
                        self._stat_row("Отверстий", str(pd["hole_count"] or 0))
                        self._stat_row("Углов", str(pd["corner_count"] or 0))

                # Right: Traceability & Templates
                with ui.column().classes("w-2/3 gap-6"):
                    # Tabs for History
                    with ui.tabs().classes("w-full text-zinc-400") as tabs:
                        t1: Any = ui.tab("История заказов")
                        t2: Any = ui.tab("Готовые паллеты")
                        t3: Any = ui.tab("Заметки")

                    with ui.tab_panels(tabs, value=t1).classes("w-full bg-transparent"):
                        with ui.tab_panel(t1):
                            await self._render_work_items(pd["sku"])
                        with ui.tab_panel(t2):
                            await self._render_pallets(pd["sku"])
                        with ui.tab_panel(t3):
                            await self._render_templates(pd["sku"])

        dialog.open()

    def _stat_row(self, label: str, value: str) -> None:
        with ui.row().classes("w-full justify-between text-xs py-1 border-b border-zinc-800/50"):
            ui.label(label).classes("text-zinc-500")
            ui.label(value).classes("text-zinc-200 font-mono")

    async def _render_work_items(self, sku: str) -> None:
        async with self.scope() as req:
            parts_system: PartLibrarySystem = await req.get(PartLibrarySystem)
            items: list[WorkItem] = parts_system.trace_work_items_for_sku(sku)

        if not items:
            ui.label("Не использовалась в заказах").classes("text-sm text-zinc-600 italic")
            return

        with ui.list().classes("w-full border border-zinc-800 rounded overflow-hidden"):
            for wi in items:
                with ui.item().classes("border-b border-zinc-800 last:border-0"):
                    with ui.item_section():
                        ui.label(wi.folder_name).classes("text-sm text-zinc-100")
                        ui.label(f"ID: {wi.id} • Sidra: {wi.sidra_number or 'N/A'}").classes(
                            "text-[10px] text-zinc-500 uppercase"
                        )
                    with ui.item_section().props("side"):
                        ui.badge(wi.status, color="zinc-700").classes("text-[10px]")

    async def _render_pallets(self, sku: str) -> None:
        async with self.scope() as req:
            parts_system: PartLibrarySystem = await req.get(PartLibrarySystem)
            pallets: list[ProductionUnit] = parts_system.trace_pallets_for_sku(sku)

        if not pallets:
            ui.label("Нет на готовых паллетах").classes("text-sm text-zinc-600 italic")
            return

        with ui.list().classes("w-full border border-zinc-800 rounded overflow-hidden"):
            for unit in pallets:
                with ui.item().classes("border-b border-zinc-800 last:border-0"):
                    with ui.item_section():
                        ui.label(unit.label_id).classes("text-sm text-zinc-100 font-mono")
                        ui.label(f"Кол-во: {unit.qty_produced}").classes(
                            "text-[10px] text-zinc-500"
                        )
                    with ui.item_section().props("side"):
                        ui.label("Склад").classes("text-[10px] text-green-500 uppercase font-bold")

    async def _render_templates(self, sku: str) -> None:
        async with self.scope() as req:
            parts_system: PartLibrarySystem = await req.get(PartLibrarySystem)
            templates: list[PartTemplate] = parts_system.list_part_templates(sku)

        with ui.column().classes("w-full gap-4"):
            with ui.row().classes("w-full justify-end"):
                ui.button("Добавить заметку", on_click=lambda: self.add_template_dialog(sku)).props(
                    "small outline color=primary"
                )

            if not templates:
                ui.label("Заметок нет").classes("text-sm text-zinc-600 italic text-center w-full")
                return

            for tmpl in templates:
                assert tmpl.id is not None
                color: str = (
                    "red-500"
                    if tmpl.severity == "critical"
                    else "amber-500"
                    if tmpl.severity == "warning"
                    else "blue-500"
                )
                with ui.card().classes(f"w-full bg-zinc-900 border-l-4 border-{color} p-3"):
                    with ui.row().classes("w-full justify-between items-start"):
                        ui.label(tmpl.message).classes("text-sm text-zinc-200 w-4/5")
                        ui.button(
                            icon="delete",
                            on_click=lambda *args, tid=tmpl.id: self.delete_template(tid),
                        ).props("flat small color=red")
                    ui.label(
                        f"От {tmpl.created_by} • {tmpl.created_at.strftime('%d.%m.%Y')}"
                    ).classes("text-[10px] text-zinc-500 mt-2")

    def add_template_dialog(self, sku: str) -> None:
        """Dialog to add a new part note/warning."""
        with ui.dialog() as d, ui.card().classes("bg-zinc-900 w-96"):
            ui.label("Добавить заметку").classes("text-lg font-bold text-zinc-100 mb-4")
            msg: Any = ui.textarea(placeholder="Текст сообщения...").classes("w-full")
            sev: Any = ui.select(
                ["info", "warning", "critical"], label="Важность", value="info"
            ).classes("w-full")

            async def submit() -> None:
                async with self.scope() as req:
                    parts_system: PartLibrarySystem = await req.get(PartLibrarySystem)
                    parts_system.create_part_template(sku, msg.value, sev.value, author="user")
                d.close()
                NotifyHelper.error("Заметка добавлена")

            with ui.row().classes("w-full justify-end mt-4"):
                ui.button("Отмена", on_click=d.close).props("flat")
                ui.button("Сохранить", on_click=submit)
        d.open()

    async def delete_template(self, template_id: int) -> None:
        async with self.scope() as req:
            parts_system: PartLibrarySystem = await req.get(PartLibrarySystem)
            parts_system.remove_part_template(template_id)
        NotifyHelper.info("Заметка удалена")

    def open_geo_search(self) -> None:
        """Dialog for Bbox-based geometrical search."""
        with ui.dialog() as d, ui.card().classes("bg-zinc-900 w-80"):
            ui.label("Поиск по геометрии").classes("text-lg font-bold text-zinc-100 mb-4")
            x: Any = ui.number(label="Ширина (X), мм", value=100)
            y: Any = ui.number(label="Высота (Y), мм", value=100)
            tol: Any = ui.number(label="Допуск, %", value=5)

            async def run_search() -> None:
                async with self.scope() as req:
                    parts_system: PartLibrarySystem = await req.get(PartLibrarySystem)
                    parts: list[Any] = parts_system.find_parts_by_geometric_similarity(
                        x.value, y.value, tol.value
                    )
                d.close()
                self._show_search_results(parts)

            ui.button("Найти аналоги", on_click=run_search).classes("w-full mt-4")
        d.open()

    def _show_search_results(self, parts: list[Any]) -> None:
        """Temporary overlay or notify if no results found."""
        if not parts:
            NotifyHelper.info("Похожих деталей не найдено")
            return
        NotifyHelper.info(f"Найдено аналогов: {len(parts)}")
        # Potentially update grid with results
