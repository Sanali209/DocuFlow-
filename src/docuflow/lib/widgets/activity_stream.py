from nicegui import ui
from sqlmodel import select

from docuflow.domain.entities.production import WorkLog
from docuflow.lib.base_widget import BaseDocuWidget


class ActivityStream(BaseDocuWidget):
    """Живая лента событий системы."""

    def __init__(self, db_engine, system_provider=None):
        super().__init__(system_provider)
        self.db_engine = db_engine

    @ui.refreshable
    def render(self) -> None:
        """Живая лента событий системы."""
        with ui.column().classes("w-full h-full gap-2 p-4"):
            ui.label("LIVE ACTIVITY").classes(
                "text-xs font-black text-indigo-400 tracking-widest mb-2"
            )

            from sqlmodel import Session

            with Session(self.db_engine) as session:
                logs = session.exec(
                    select(WorkLog).order_by(WorkLog.created_at.desc()).limit(15)
                ).all()

                if not logs:
                    ui.label("No recent activity").classes("text-gray-500 italic text-sm")
                    return

                for log in logs:
                    color = "indigo"
                    icon = "info"
                    if "[MATERIAL_INCIDENT]" in log.message or "[BREAKDOWN]" in log.message:
                        color = "red"
                        icon = "warning"
                    elif "FULFILLED" in log.message:
                        color = "emerald"
                        icon = "check_circle"

                    with ui.row().classes(
                        "w-full items-start gap-3 p-2 bg-white/5 rounded-lg border border-white/5"
                    ):
                        ui.icon(icon, color=color, size="16px").classes("mt-1")
                        with ui.column().classes("gap-0 flex-1"):
                            ui.label(log.message).classes("text-xs text-slate-200 leading-tight")
                            with ui.row().classes("items-center gap-2"):
                                ui.label(log.created_at.strftime("%H:%M:%S")).classes(
                                    "text-[9px] text-slate-500"
                                )
                                if log.node_id:
                                    ui.badge(log.node_id).props(
                                        f"color={color}-900 size=xs"
                                    ).classes("text-[8px]")

        # Auto-refresh every 10 seconds
        ui.timer(10.0, self.render.refresh, once=True)
