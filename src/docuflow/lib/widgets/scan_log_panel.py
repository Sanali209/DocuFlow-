from typing import Any

from nicegui import ui
from sqlalchemy import Engine
from sqlmodel import Session, desc, select

from docuflow.domain.entities.production import WorkLog, WorkLogType
from docuflow.lib.base_widget import BaseDocuWidget


class ScanLogPanel(BaseDocuWidget):
    """
    Reactive log panel for displaying the last N production events.
    """

    def __init__(self, engine: Engine, limit: int = 50, system_scope: Any = None):
        super().__init__(system_scope)
        self.engine = engine
        self.limit = limit
        self.container: Any = None

    def render(self):
        """Рендерит панель лога."""
        with ui.column().classes(
            "w-full gap-2 p-4 bg-slate-800/60 rounded-2xl border border-slate-700/50"
        ) as self.container:
            ui.label("SYSTEM ACTIVITY LOG").classes(
                "text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2"
            )
            self.log_area = ui.column().classes(
                "w-full gap-2 overflow-y-auto max-h-[400px] pr-2 custom-scrollbar"
            )
            self.refresh()

        # 5 second polling interval as requested
        ui.timer(5.0, self.refresh)

    def refresh(self):
        """Fetch and render the latest logs."""

        async def do_refresh():
            async with self.scope() as req:
                session = await req.get(Session)
                logs = session.exec(
                    select(WorkLog).order_by(desc(WorkLog.created_at)).limit(self.limit)
                ).all()

                self.log_area.clear()
                with self.log_area:
                    if not logs:
                        ui.label("Awaiting cluster Activity...").classes(
                            "text-slate-600 italic text-xs py-4"
                        )
                    for log in logs:
                        self._render_log_item(log)

        # Silent refresh for background polling
        ui.timer(0, do_refresh, once=True)

    def _render_log_item(self, log: WorkLog):
        """Render a single log entry with a badge."""
        with ui.row().classes(
            "w-full items-center gap-3 p-2 hover:bg-white/5 rounded-lg "
            "transition-colors border-l-2 border-transparent hover:border-indigo-500"
        ):
            # Timestamp
            ui.label(log.created_at.strftime("%H:%M:%S")).classes(
                "text-[10px] font-mono text-slate-500 w-16"
            )

            # Badge
            color = self._get_log_color(log.log_type)
            ui.badge(log.log_type.value.upper(), color=color).classes(
                "text-[8px] font-bold px-2 py-0.5"
            )

            # Message
            ui.label(log.message).classes("text-xs text-slate-300 flex-1 truncate")

            if log.node_id:
                ui.label(log.node_id).classes("text-[10px] text-slate-600 font-mono")

    def _get_log_color(self, log_type: WorkLogType) -> str:
        if log_type == WorkLogType.SCAN_ERROR:
            return "red-500"
        if log_type == WorkLogType.FILE_CHANGED:
            return "orange-600"
        if log_type == WorkLogType.EMPTY_FOLDER:
            return "amber-500"
        if log_type == WorkLogType.NS_MIRROR:
            return "blue-500"
        if log_type == WorkLogType.STATUS_CHANGE:
            return "emerald-500"
        return "slate-600"
