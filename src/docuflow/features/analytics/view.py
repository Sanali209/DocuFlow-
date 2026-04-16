from nicegui import ui
from sqlmodel import Session, func, select

from docuflow.domain.entities.production import ProductionUnit, TaskItem, TaskItemStatus, WorkItem
from docuflow.features.core.views import ViewInfo, ViewRegistry


def register_analytics_view():
    """Register the analytics dashboard view."""
    ViewRegistry.register(
        ViewInfo(
            name="analytics",
            label="Analytics",
            icon="analytics",
            render_fn=analytics_view,
            dependencies=[Session],
            is_async=True,
        )
    )


async def analytics_view(session: Session) -> None:
    """Provides high-level KPI and performance analytics."""

    with ui.column().classes("w-full h-full p-8 gap-6"):
        ui.label("Analytics Dashboard").classes("text-3xl font-bold text-white mb-2")

        try:
            # Gather metrics
            total_work_items = session.exec(select(func.count(WorkItem.id))).one()
            total_tasks = session.exec(select(func.count(TaskItem.id))).one()
            completed_tasks = session.exec(
                select(func.count(TaskItem.id)).where(TaskItem.status == TaskItemStatus.DONE)
            ).one()
            total_pallets = session.exec(select(func.count(ProductionUnit.id))).one()
            total_parts_produced = (
                session.exec(select(func.sum(ProductionUnit.qty_produced))).one() or 0
            )

            # --- NEW: Calculation of Drift KPI ---
            stmt_drift = select(TaskItem).where(TaskItem.status == TaskItemStatus.DONE)
            done_tasks = session.exec(stmt_drift).all()
            total_drift = 0.0
            count_drift = 0
            for t in done_tasks:
                if t.estimated_minutes and t.actual_minutes:
                    total_drift += (
                        (t.actual_minutes - t.estimated_minutes) / t.estimated_minutes * 100
                    )
                    count_drift += 1
            avg_drift = round(total_drift / count_drift, 1) if count_drift > 0 else 0.0

            round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
        except Exception as e:
            ui.label(f"Failed to load metrics: {e}").classes("text-red-400")
            return

        with ui.row().classes("w-full gap-6"):
            # Metric Card 1
            with ui.column().classes("flex-1 p-6 rounded-2xl card"):
                ui.label("TOTAL WORK ITEMS").classes(
                    "text-slate-400 font-bold text-xs tracking-tighter"
                )
                ui.label(str(total_work_items)).classes("text-cyan-400 text-4xl font-black mt-2")

            # Metric Card 2 (DRIFT)
            drift_color = "emerald" if avg_drift <= 5 else "orange" if avg_drift <= 20 else "red"
            with ui.column().classes("flex-1 p-6 rounded-2xl card"):
                ui.label("AVG PRODUCTION DRIFT").classes(
                    "text-slate-400 font-bold text-xs tracking-tighter"
                )
                ui.label(f"{'+' if avg_drift > 0 else ''}{avg_drift}%").classes(
                    f"text-{drift_color}-400 text-4xl font-black mt-2"
                )
                ui.label(f"Based on {count_drift} completed tasks").classes(
                    "text-slate-500 text-sm mt-2"
                )

            # Metric Card 3
            with ui.column().classes("flex-1 p-6 rounded-2xl card"):
                ui.label("TOTAL FINISHED PARTS").classes(
                    "text-slate-400 font-bold text-xs tracking-tighter"
                )
                ui.label(str(total_parts_produced)).classes(
                    "text-orange-400 text-4xl font-black mt-2"
                )
                ui.label(f"Across {total_pallets} Pallets").classes("text-slate-500 text-sm mt-2")

        # --- CHARTS SECTION ---
        with ui.row().classes("w-full gap-6 mt-6"):
            # Chart 1: Status Distribution
            with ui.column().classes("flex-1 p-6 rounded-2xl card"):
                ui.label("TASK STATUS DISTRIBUTION").classes(
                    "text-slate-400 text-xs font-bold mb-4"
                )

                # Dynamic data for chart
                status_counts = {}
                for s in TaskItemStatus:
                    count = session.exec(
                        select(func.count(TaskItem.id)).where(TaskItem.status == s)
                    ).one()
                    if count > 0:
                        status_counts[s.value.upper()] = count

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
                                "data": [{"value": v, "name": k} for k, v in status_counts.items()],
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
