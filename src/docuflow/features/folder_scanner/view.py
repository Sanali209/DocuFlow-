import logging
from typing import TYPE_CHECKING, Any

from nicegui import ui
from sqlalchemy import Engine
from sqlmodel import Session

from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.folder_scanner.system import FolderScannerSystem
from docuflow.infrastructure.config import Config
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ns_mirror_status import NSMirrorStatus
from docuflow.lib.widgets.scan_log_panel import ScanLogPanel
from docuflow.lib.widgets.ui_utils import (
    NotifyHelper,
    get_role_indicator_color,
    get_sync_indicator_color,
)


def register_scanner_view():
    from docuflow.sdk import SDK

    ViewRegistry.register(
        ViewInfo(
            name="scanner",
            label="Scanner",
            icon="scanner",
            render_fn=folder_scanner_view_wrapper,
            dependencies=[SDK, Config, Engine],
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


if TYPE_CHECKING:
    from docuflow.sdk import SDK

logger = logging.getLogger("docuflow.folder_scanner.view")


async def folder_scanner_view_wrapper(
    sdk: "SDK", config: Config, engine: Engine, system_scope: Any, layout: Any, **kwargs
):
    """Wrapper to instantiate and render the ScannerView."""
    view = ScannerView(sdk, config, engine, system_scope, layout=layout)
    await view.render()


class ScannerView(BaseDocuWidget):
    def __init__(
        self, sdk: "SDK", config: Config, engine: Engine, system_scope: Any, layout: Any = None
    ):
        super().__init__(system_scope)
        self.sdk = sdk
        self.config = config
        self.engine = engine
        self.layout = layout

    @ui.refreshable
    async def render(self):
        """Render the scanner management interface."""
        async with self.scope() as req:
            scanner = await req.get(FolderScannerSystem)

        with ui.column().classes("w-full gap-8"):
            # --- HEADER SECTION ---
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("gap-1"):
                    ui.label("Folder Ingestion & NC Mirror").classes(
                        "text-3xl font-bold text-white"
                    )
                    with ui.row().classes("items-center gap-2"):
                        # Pulsing indicator for Master status
                        is_master = self.sdk.orchestrator.is_leader
                        color = get_role_indicator_color(is_master)
                        pulse_class = "animate-pulse" if is_master else ""
                        ui.icon("circle", color=color, size="12px").classes(pulse_class)
                        ui.label(
                            f"{'MASTER' if is_master else 'SLAVE'} NODE: {self.config.node_id}"
                        ).classes(f"text-xs font-mono font-bold text-{color}")

                # Everyone can "Scan Now" as requested
                async def force_scan():
                    NotifyHelper.info("Manual Scan Triggered...")
                    result = scanner.scan_now()
                    if result and hasattr(result, "__await__"):
                        await result
                    NotifyHelper.info("Scan request processed by Master")

                ui.button("SCAN NOW", icon="sync", on_click=force_scan).classes(
                    "vibrant-btn rounded-xl px-12 h-14"
                )

            # --- STATUS GRID ---
            with ui.row().classes("w-full gap-6 flex-wrap"):
                # Scanner Status Card
                with ui.card().classes(
                    "flex-1 min-w-[300px] bg-white/5 border border-white/10 rounded-3xl p-6"
                ):
                    ui.label("SCANNER STATUS").classes(
                        "text-xs font-bold text-slate-500 uppercase tracking-widest mb-4"
                    )
                    async with self.scope() as req:
                        fresh_scanner = await req.get(FolderScannerSystem)
                        status = fresh_scanner.get_ingestion_status()

                    color = get_sync_indicator_color(status["is_active"])
                    pulse_class = "animate-pulse" if status["is_active"] else ""
                    with ui.row().classes("items-center gap-2 mb-2"):
                        ui.icon("circle", color=color, size="12px").classes(pulse_class)
                        ui.label("ACTIVE" if status["is_active"] else "IDLE").classes(
                            f"text-{color} font-bold text-sm"
                        )
                    with ui.column().classes("gap-1 text-xs text-slate-400"):
                        if status["last_scan_at"]:
                            ui.label(
                                f"Last scan: {status['last_scan_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                        else:
                            ui.label("Last scan: Never")
                        ui.label(f"Files found: {status['items_found']}")
                        ui.label(
                            "Status: Scanning SIDRA folder"
                            if status["is_active"]
                            else "Status: Idle"
                        )

                # NS Mirror Status Card
                with ui.card().classes(
                    "flex-1 min-w-[300px] bg-white/5 border border-white/10 rounded-3xl p-6"
                ):
                    ui.label("LOCAL NS SYNC STATUS").classes(
                        "text-xs font-bold text-slate-500 uppercase tracking-widest mb-4"
                    )
                    # Get real NS Mirror status from database
                    async with self.scope() as req:
                        from sqlmodel import desc, select

                        from docuflow.domain.entities.production import WorkLog, WorkLogType

                        session = await req.get(Session)

                        # Get latest NS Mirror log
                        latest_mirror_log = session.exec(
                            select(WorkLog)
                            .where(WorkLog.log_type == WorkLogType.NS_MIRROR)
                            .where(WorkLog.node_id == self.config.node_id)
                            .order_by(desc(WorkLog.created_at))
                        ).first()

                        # Count mirrored files
                        mirrored_count = session.exec(
                            select(WorkLog)
                            .where(WorkLog.log_type == WorkLogType.NS_MIRROR)
                            .where(WorkLog.node_id == self.config.node_id)
                        ).all()

                        with ui.row().classes("items-center gap-2 mb-2"):
                            color = get_sync_indicator_color(bool(latest_mirror_log))
                            ui.icon("circle", color=color, size="12px").classes(
                                "animate-pulse" if latest_mirror_log else ""
                            )
                            ui.label("ACTIVE" if latest_mirror_log else "IDLE").classes(
                                f"text-{color} font-bold text-sm"
                            )

                        with ui.column().classes("gap-1 text-xs text-slate-400"):
                            if latest_mirror_log:
                                ui.label(
                                    f"Last sync: {latest_mirror_log.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                                )
                            else:
                                ui.label("Last sync: Never")
                            ui.label(f"Files mirrored: {len(mirrored_count)}")

                # Dashboard Overview Card
                with ui.card().classes(
                    "flex-1 min-w-[300px] bg-white/5 border border-white/10 rounded-3xl p-6"
                ):
                    ui.label("CURRENT BUCKET STATUS").classes(
                        "text-xs font-bold text-slate-500 uppercase tracking-widest mb-4"
                    )
                    mirror_status = NSMirrorStatus(
                        self.engine, self.config.node_id, system_scope=self.system_scope
                    )
                    mirror_status.render()

                # Scan Settings Snippet - READ FROM DATABASE
                with ui.card().classes(
                    "flex-1 min-w-[300px] bg-white/5 border border-white/10 rounded-3xl p-6"
                ):
                    ui.label("SCANNER CONFIG").classes(
                        "text-xs font-bold text-slate-500 uppercase tracking-widest mb-4"
                    )
                    # Read settings from database for this node
                    async with self.scope() as req:
                        fresh_scanner = await req.get(FolderScannerSystem)
                        settings = fresh_scanner.fetch_scanner_settings()

                    with ui.column().classes("gap-2"):
                        with ui.row().classes("w-full justify-between items-center text-xs"):
                            ui.label("SIDRA PATH").classes("text-slate-400")
                            ui.label(settings.sidra_scan_path or "Not Configured").classes(
                                "font-mono text-slate-300"
                            )
                        with ui.row().classes("w-full justify-between items-center text-xs"):
                            ui.label("MIHTAV PATH").classes("text-slate-400")
                            ui.label(settings.mihtav_scan_path or "Not Configured").classes(
                                "font-mono text-slate-300"
                            )
                        with ui.row().classes("w-full justify-between items-center text-xs"):
                            ui.label("OTHER PATH").classes("text-slate-400")
                            ui.label(settings.other_scan_path or "Not Configured").classes(
                                "font-mono text-slate-300"
                            )
                        with ui.row().classes("w-full justify-between items-center text-xs"):
                            ui.label("POLL INTERVAL").classes("text-slate-400")
                            ui.label(f"{settings.poll_interval_seconds} seconds").classes(
                                "text-slate-300"
                            )
                        with ui.row().classes("w-full justify-between items-center text-xs"):
                            ui.label("NS MIRROR INTERVAL").classes("text-slate-400")
                            ui.label(f"{settings.ns_mirror_interval_seconds} seconds").classes(
                                "text-slate-300"
                            )
                        with ui.row().classes("w-full justify-between items-center text-xs"):
                            ui.label("NS MIRROR TIMEOUT").classes("text-slate-400")
                            ui.label(f"{settings.ns_mirror_copy_timeout_s} seconds").classes(
                                "text-slate-300"
                            )
                        with ui.row().classes(
                            "w-full justify-between items-center text-xs pt-2 border-t border-white/5"
                        ):
                            ui.label("LOCAL NS MIRROR").classes("text-indigo-400 font-bold")
                            ui.label(settings.local_ns_path or "OFF").classes(
                                "font-mono text-indigo-300"
                            )
                        with ui.row().classes("w-full justify-between items-center text-xs"):
                            ui.label("ENABLED").classes("text-slate-400")
                            ui.label("Yes" if settings.enabled else "No").classes(
                                "font-mono text-slate-300"
                            )
                        with ui.row().classes("w-full justify-between items-center text-xs"):
                            ui.label("DEFAULT PROJECT").classes("text-slate-400")
                            ui.label(settings.default_project_name or "GENERAL").classes(
                                "font-mono text-slate-300"
                            )

            # --- LOG PANEL ---
            with ui.column().classes("w-full"):
                ui.label("Real-time synchronization logs").classes(
                    "text-lg font-medium text-slate-400 ml-2 mb-2"
                )
                log_panel = ScanLogPanel(self.engine, system_scope=self.system_scope)
                log_panel.render()
