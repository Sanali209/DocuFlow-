from nicegui import ui
from sqlalchemy import Engine
from sqlmodel import Session, func, select

from docuflow.domain.entities.production import WorkerBucketEntry, WorkLog, WorkLogType


class NSMirrorStatus:
    """
    Compact status widget showing local NC synchronization health.
    """

    def __init__(self, engine: Engine, node_id: str):
        self.engine = engine
        self.node_id = node_id

    def build(self):
        with ui.card().classes("w-full bg-slate-900/60 rounded-3xl border border-white/10 p-6"):
            with ui.row().classes("w-full items-center justify-between mb-2"):
                ui.label("LOCAL NS SYNC").classes(
                    "text-xs font-bold text-indigo-300 opacity-60 tracking-widest uppercase"
                )
                ui.icon("sync", color="indigo").classes("animate-spin-slow")

            self.main_status = ui.label("Refreshing...").classes("text-lg font-bold text-white")
            self.sub_status = ui.label("").classes("text-xs text-slate-500 font-mono")

            ui.timer(5.0, self.refresh)
            self.refresh()

    def refresh(self):
        try:
            with Session(self.engine) as session:
                # 1. Active Bucket Entries
                bucket_count = session.exec(
                    select(func.count(WorkerBucketEntry.id)).where(
                        WorkerBucketEntry.node_id == self.node_id
                    )
                ).one()

                # 2. FILE_CHANGED warnings on current node
                # Note: This is an approximation of "stale" files in bucket
                # We fetch latest warnings from WorkLog for this node
                stale_count = session.exec(
                    select(func.count(WorkLog.id))
                    .where(WorkLog.log_type == WorkLogType.FILE_CHANGED)
                    .where(WorkLog.node_id == self.node_id)
                ).one()

                if bucket_count == 0:
                    self.main_status.text = "Idle"
                    self.sub_status.text = "No NC tasks assigned"
                elif stale_count > 0:
                    self.main_status.text = f"Warning: {stale_count} Stale"
                    self.main_status.classes("text-red-400")
                    self.sub_status.text = f"{bucket_count} files in total bucket"
                else:
                    self.main_status.text = "Synchronized"
                    self.main_status.classes("text-white")
                    self.sub_status.text = f"{bucket_count} target files matching network"

        except Exception:
            pass
