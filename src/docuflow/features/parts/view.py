from nicegui import ui

from docuflow.domain.entities.production import PartLibrary, PartTemplate
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.parts.system import PartLibrarySystem
from docuflow.lib.widgets.part_preview import PartPreview


def register_parts_view():
    """Register the parts library view."""
    ViewRegistry.register(
        ViewInfo(
            name="parts",
            label="Parts",
            icon="extension",
            render_fn=parts_view_wrapper,
            dependencies=[PartLibrarySystem],
            is_async=True,
        )
    )


async def parts_view_wrapper(parts_system: PartLibrarySystem):
    """Wrapper to instantiate and render the PartLibraryView."""
    view = PartLibraryView(parts_system)
    await view.render()


class PartLibraryView:
    """
    Electronic catalog of all unique parts scanned by the system.

    Features:
    - Interactive grid with SKU thumbnails.
    - Advanced filtering (SKU, Material, Bbox range).
    - Modal details with statistics and history.
    """

    def __init__(self, parts_system: PartLibrarySystem):
        self.parts_system = parts_system
        self.grid = None
        self.search_query = ""
        self.mat_filter = None
        self.bbox_x_min = 0
        self.bbox_x_max = 2000

    @ui.refreshable
    async def render(self):
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
                        placeholder="Поиск по SKU...", on_change=self.render.refresh
                    ).bind_value(self, "search_query").classes("w-64 bg-zinc-900 border-zinc-800")

                    ui.button("Гео-поиск", icon="straighten", on_click=self.open_geo_search).props(
                        "flat color=primary"
                    )

                    ui.button(icon="refresh", on_click=self.render.refresh).props("flat")

            # --- Main Content (Grid) ---
            self.grid = ui.grid(columns=6).classes("w-full gap-4")
            await self._build_parts_grid()

            # Auto-refresh every 15 seconds
            ui.timer(15.0, self.render.refresh, once=True)

    async def _build_parts_grid(self):
        """Internal helper to build the grid content."""
        parts = self.parts_system.list_parts(
            sku_filter=self.search_query if len(self.search_query) >= 2 else None, limit=50
        )

        if not parts:
            with self.grid:
                ui.label("Детали не найдены").classes(
                    "col-span-full text-center text-zinc-600 mt-12 py-8 border-2 border-dashed border-zinc-800 rounded-lg"
                )
            return

        with self.grid:
            for part in parts:
                with (
                    ui.card()
                    .classes(
                        "group relative overflow-hidden bg-zinc-900 border-zinc-800 hover:border-blue-500/50 transition-all cursor-pointer p-3"
                    )
                    .on("click", lambda p=part: self.open_part_details(p))
                ):
                    # SVG Thumbnail
                    PartPreview(part.svg_preview_path).render()

                    # SKU & Metrics
                    with ui.column().classes("mt-2 gap-0"):
                        ui.label(part.sku).classes(
                            "text-xs font-bold truncate text-zinc-200 group-hover:text-blue-400"
                        )
                        ui.label(f"{part.bbox_x:.1f} × {part.bbox_y:.1f} мм").classes(
                            "text-[10px] text-zinc-500 uppercase tracking-tighter"
                        )

                    # Hover Overlay
                    with ui.row().classes(
                        "absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                    ):
                        ui.icon("info", size="16px").classes("text-blue-500")

    def open_part_details(self, part: PartLibrary):
        """Open detailed modal for a specific part."""
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
                    ui.label(part.sku).classes("text-xl font-bold text-zinc-100")
                    ui.label(
                        f"Версия {part.version} • Впервые замечена: {part.first_seen_at.strftime('%d.%m.%Y')}"
                    ).classes("text-xs text-zinc-500")
                ui.button(icon="close", on_click=dialog.close).props("flat color=white")

            with ui.row().classes("w-full p-6 gap-8"):
                # Left: Large Preview & Stats
                with ui.column().classes("w-1/3 gap-4"):
                    PartPreview(part.svg_preview_path, size="280px").render()

                    with ui.card().classes("w-full bg-zinc-900/50 border-zinc-800 p-4"):
                        ui.label("Метрики").classes(
                            "text-xs font-bold uppercase text-zinc-500 mb-2"
                        )
                        self._stat_row("Габариты", f"{part.bbox_x:.1f} × {part.bbox_y:.1f} мм")
                        self._stat_row("Контуров", str(part.contour_count or 0))
                        self._stat_row("Отверстий", str(part.hole_count or 0))
                        self._stat_row("Углов", str(part.corner_count or 0))

                # Right: Traceability & Templates
                with ui.column().classes("w-2/3 gap-6"):
                    # Tabs for History
                    with ui.tabs().classes("w-full text-zinc-400") as tabs:
                        t1 = ui.tab("История заказов")
                        t2 = ui.tab("Готовые паллеты")
                        t3 = ui.tab("Заметки")

                    with ui.tab_panels(tabs, value=t1).classes("w-full bg-transparent"):
                        with ui.tab_panel(t1):
                            self._render_work_items(part.sku)
                        with ui.tab_panel(t2):
                            self._render_pallets(part.sku)
                        with ui.tab_panel(t3):
                            self._render_templates(part.sku)

        dialog.open()

    def _stat_row(self, label: str, value: str):
        with ui.row().classes("w-full justify-between text-xs py-1 border-b border-zinc-800/50"):
            ui.label(label).classes("text-zinc-500")
            ui.label(value).classes("text-zinc-200 font-mono")

    def _render_work_items(self, sku: str):
        items = self.parts_system.get_work_items_for_part(sku)
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

    def _render_pallets(self, sku: str):
        pallets = self.parts_system.get_production_units_for_part(sku)
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

    def _render_templates(self, sku: str):
        templates = self.parts_system.get_templates(sku)

        with ui.column().classes("w-full gap-4"):
            with ui.row().classes("w-full justify-end"):
                ui.button("Добавить заметку", on_click=lambda: self.add_template_dialog(sku)).props(
                    "small outline color=primary"
                )

            if not templates:
                ui.label("Заметок нет").classes("text-sm text-zinc-600 italic text-center w-full")
                return

            for tmpl in templates:
                color = (
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
                            icon="delete", on_click=lambda t=tmpl: self.delete_template(t)
                        ).props("flat small color=red")
                    ui.label(
                        f"От {tmpl.created_by} • {tmpl.created_at.strftime('%d.%m.%Y')}"
                    ).classes("text-[10px] text-zinc-500 mt-2")

    def add_template_dialog(self, sku: str):
        """Dialog to add a new part note/warning."""
        with ui.dialog() as d, ui.card().classes("bg-zinc-900 w-96"):
            ui.label("Добавить заметку").classes("text-lg font-bold text-zinc-100 mb-4")
            msg = ui.textarea(placeholder="Текст сообщения...").classes("w-full")
            sev = ui.select(
                ["info", "warning", "critical"], label="Важность", value="info"
            ).classes("w-full")

            async def submit():
                self.parts_system.create_template(sku, msg.value, sev.value, author="user")
                d.close()
                # Simplified refresh: reopening details would work but here we just notify
                ui.notify("Заметка добавлена")

            with ui.row().classes("w-full justify-end mt-4"):
                ui.button("Отмена", on_click=d.close).props("flat")
                ui.button("Сохранить", on_click=submit)
        d.open()

    async def delete_template(self, template: PartTemplate):
        self.parts_system.delete_template(template.id)
        ui.notify("Заметка удалена")

    def open_geo_search(self):
        """Dialog for Bbox-based geometrical search."""
        with ui.dialog() as d, ui.card().classes("bg-zinc-900 w-80"):
            ui.label("Поиск по геометрии").classes("text-lg font-bold text-zinc-100 mb-4")
            x = ui.number(label="Ширина (X), мм", value=100)
            y = ui.number(label="Высота (Y), мм", value=100)
            tol = ui.number(label="Допуск, %", value=5)

            async def run_search():
                parts = self.parts_system.find_by_bbox(x.value, y.value, tol.value)
                d.close()
                self._show_search_results(parts)

            ui.button("Найти аналоги", on_click=run_search).classes("w-full mt-4")
        d.open()

    def _show_search_results(self, parts):
        """Temporary overlay or notify if no results found."""
        if not parts:
            ui.notify("Похожих деталей не найдено", color="negative")
            return
        ui.notify(f"Найдено аналогов: {len(parts)}")
        # Potentially update grid with results
