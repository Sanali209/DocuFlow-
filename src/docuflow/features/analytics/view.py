from nicegui import ui
from sqlmodel import Session, func, select

from docuflow.domain.entities.production import ProductionUnit, TaskItem, WorkItem


async def analytics_view(session: Session) -> None:
    """Provides high-level KPI and performance analytics."""

    with ui.column().classes("w-full h-full p-8 gap-6"):
        ui.label("Analytics Dashboard").classes("text-3xl font-bold text-white mb-2")

        try:
            # Gather metrics
            total_work_items = session.exec(select(func.count(WorkItem.id))).one()
            total_tasks = session.exec(select(func.count(TaskItem.id))).one()
            completed_tasks = session.exec(
                select(func.count(TaskItem.id)).where(TaskItem.status == "completed")
            ).one()
            total_pallets = session.exec(select(func.count(ProductionUnit.id))).one()
            total_parts_produced = (
                session.exec(select(func.sum(ProductionUnit.qty_produced))).one() or 0
            )

            completion_rate = round(
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1
            )
        except Exception as e:
            ui.label(f"Failed to load metrics: {e}").classes("text-red-400")
            return

        with ui.row().classes("w-full gap-6"):
            # Metric Card 1
            with ui.column().classes("flex-1 p-6 rounded-2xl glass-card relative overflow-hidden"):
                ui.element("div").classes(
                    "absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl"
                )
                ui.label("TOTAL WORK ITEMS (NAREDS)").classes(
                    "text-slate-500 font-bold text-xs tracking-tighter"
                )
                ui.label(str(total_work_items)).classes("text-blue-400 text-4xl font-black mt-2")

            # Metric Card 2
            with ui.column().classes("flex-1 p-6 rounded-2xl glass-card relative overflow-hidden"):
                ui.element("div").classes(
                    "absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl"
                )
                ui.label("TASK COMPLETION RATE").classes(
                    "text-slate-500 font-bold text-xs tracking-tighter"
                )
                ui.label(f"{completion_rate}%").classes("text-emerald-400 text-4xl font-black mt-2")
                ui.label(f"{completed_tasks} / {total_tasks} Tasks").classes(
                    "text-slate-500 text-sm mt-2"
                )

            # Metric Card 3
            with ui.column().classes("flex-1 p-6 rounded-2xl glass-card relative overflow-hidden"):
                ui.element("div").classes(
                    "absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full blur-3xl"
                )
                ui.label("TOTAL FINISHED PARTS").classes(
                    "text-slate-500 font-bold text-xs tracking-tighter"
                )
                ui.label(str(total_parts_produced)).classes(
                    "text-orange-400 text-4xl font-black mt-2"
                )
                ui.label(f"Across {total_pallets} Pallets").classes("text-slate-500 text-sm mt-2")

        # Placeholder for Charts
        with ui.column().classes(
            "w-full mt-6 p-6 rounded-2xl glass-card items-center justify-center min-h-[300px] border border-white/5"
        ):
            ui.icon("monitoring", color="indigo").classes("text-6xl opacity-50 mb-4")
            ui.label("Production Trends Chart").classes("text-xl font-bold text-indigo-400")
            ui.label(
                "Detailed drift metrics and time tracking visualizations will be embedded here in the future."
            ).classes("text-sm text-slate-500")
            ui.button(
                "Refresh Data", on_click=lambda: ui.notify("Data synced", color="positive")
            ).classes("mt-4 rounded-xl px-8 vibrant-btn text-white")
