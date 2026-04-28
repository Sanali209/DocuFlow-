from typing import Any

from nicegui import ui

from docuflow.features.analytics.system import AnalyticsSystem
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.kpi_card import KPICard, KPIGrid
from docuflow.lib.widgets.ui_utils import get_kpi_color


def register_analytics_view():
    """Register the analytics dashboard view."""
    ViewRegistry.register(
        ViewInfo(
            name="analytics",
            label="Analytics",
            icon="analytics",
            render_fn=analytics_view_wrapper,
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def analytics_view_wrapper(system_scope: Any, layout: Any, **kwargs):
    """Wrapper for the class-based AnalyticsView."""
    view = AnalyticsView(system_scope, layout=layout)
    await view.render()


class AnalyticsView(BaseDocuWidget):
    """Provides high-level KPI and performance analytics."""

    def __init__(self, system_scope: Any, layout: Any = None):
        super().__init__(system_scope)
        self.layout = layout

    async def render(self) -> None:
        """Render the analytics dashboard."""
        with ui.column().classes("w-full h-full p-8 gap-6"):
            ui.label("Analytics Dashboard").classes("text-3xl font-bold text-white mb-2")

            try:
                async with self.scope() as req:
                    system = await req.get(AnalyticsSystem)
                    metrics = system.get_dashboard_metrics()

                    total_work_items = metrics["total_work_items"]
                    total_tasks = metrics["total_tasks"]
                    total_pallets = metrics["total_pallets"]
                    total_parts_produced = metrics["total_parts_produced"]
                    avg_drift = metrics["avg_drift"]
                    count_drift = metrics["count_drift"]
                    completion_rate = metrics["completion_rate"]
                    status_counts = metrics["status_counts"]
            except Exception as e:
                ui.label(f"Failed to load metrics: {e}").classes("text-red-400")
                return

            drift_color = get_kpi_color(avg_drift)

            KPIGrid(
                kpis=[
                    KPICard(
                        label="Total Work Items",
                        value=str(total_work_items),
                        subtitle=f"Completion rate: {completion_rate}%",
                        icon="inventory_2",
                        icon_color="cyan",
                    ),
                    KPICard(
                        label="Avg Production Drift",
                        value=f"{'+' if avg_drift > 0 else ''}{avg_drift}%",
                        subtitle=f"Based on {count_drift} tasks",
                        icon="trending_up" if avg_drift > 0 else "trending_down",
                        icon_color=drift_color,
                        accent_color=drift_color,
                    ),
                    KPICard(
                        label="Total Finished Parts",
                        value=str(total_parts_produced),
                        subtitle=f"Across {total_pallets} Pallets",
                        icon="precision_manufacturing",
                        icon_color="orange",
                    ),
                ]
            ).render()

            # --- CHARTS SECTION ---
            with ui.row().classes("w-full gap-6 mt-6"):
                # Chart 1: Status Distribution
                with ui.column().classes("flex-1 p-6 rounded-2xl card"):
                    ui.label("TASK STATUS DISTRIBUTION").classes(
                        "text-slate-400 text-xs font-bold mb-4"
                    )

                    ui.echart(
                        {
                            "tooltip": {"trigger": "item"},
                            "series": [
                                {
                                    "type": "pie",
                                    "radius": ["40%", "70%"],
                                    "avoidLabelOverlap": False,
                                    "itemStyle": {
                                        "borderRadius": 10,
                                        "borderColor": "#0f172a",
                                        "borderWidth": 2,
                                    },
                                    "label": {"show": False},
                                    "data": [
                                        {"value": v, "name": k} for k, v in status_counts.items()
                                    ],
                                }
                            ],
                        }
                    ).classes("h-64")

                # Chart 2: Output Trend (Mocked dates for now)
                with ui.column().classes("flex-grow-[2] p-6 rounded-2xl card"):
                    ui.label("PARTS PRODUCED (LAST 7 DAYS)").classes(
                        "text-slate-400 text-xs font-bold mb-4"
                    )
                    ui.echart(
                        {
                            "xAxis": {
                                "type": "category",
                                "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                            },
                            "yAxis": {"type": "value"},
                            "series": [
                                {
                                    "data": [120, 200, 150, 80, 70, 110, 130],
                                    "type": "bar",
                                    "itemStyle": {"color": "#14b8a6"},
                                }
                            ],
                        }
                    ).classes("h-64")
