from collections.abc import Callable
from typing import Any

from nicegui import ui
from sqlmodel import Session

from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.features.admin.system import AdminSystem
from docuflow.features.analytics.system import AnalyticsSystem
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.activity_stream import ActivityStream


def register_dashboard_view() -> None:
    """Register the dashboard view in the global registry."""
    ViewRegistry.register(
        ViewInfo(
            name="dashboard",
            label="Dashboard",
            icon="dashboard",
            render_fn=dashboard_view_wrapper,
            dependencies=[P2POrchestrator, AdminSystem],
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def dashboard_view_wrapper(
    orchestrator: P2POrchestrator, admin_system: AdminSystem, system_scope: Callable, layout: Any
) -> None:
    """Wrapper to instantiate and render the DashboardView."""
    view: DashboardView = DashboardView(orchestrator, admin_system, system_scope, layout)
    await view.render()


class DashboardView(BaseDocuWidget):
    """Providing the centralized cluster overview and health summary."""

    def __init__(
        self,
        orchestrator: P2POrchestrator,
        admin_system: AdminSystem,
        system_scope: Callable,
        layout: Any,
    ) -> None:
        super().__init__(system_scope)
        self.orchestrator = orchestrator
        self.admin_system = admin_system
        self.layout = layout

    async def render(self) -> None:
        """Render the dashboard UI."""
        # 0. FETCH DATA
        req: Any
        async with self.scope() as req:
            fresh_admin: AdminSystem = await req.get(AdminSystem)
            nodes: list[dict[str, Any]] = fresh_admin.get_cluster_nodes()
            analytics: AnalyticsSystem = await req.get(AnalyticsSystem)
            metrics: dict[str, Any] = analytics.get_cluster_overview_metrics()

            wi_count: Any = metrics["work_item_count"]
            incident_count: Any = metrics["incident_count"]
            pallet_count: Any = metrics["stock_pallet_count"]
            session: Session = await req.get(Session)

        ui.label("Cluster Management Hub").classes("text-3xl font-bold text-white mb-4")

        # --- TOP KPI ROW ---
        with ui.row().classes("w-full gap-6"):
            # 1. PEER COUNT
            with ui.column().classes("flex-1 p-6 rounded-2xl card"):
                ui.label("CLUSTERS NODES").classes(
                    "text-slate-400 font-bold text-xs tracking-tighter"
                )
                ui.label(f"{len(nodes)} ONLINE").classes(
                    "text-emerald-400 text-4xl font-black mt-2"
                )
                ui.label("P2P Mesh Synchronized").classes(
                    "text-slate-500 text-[10px] mt-4 uppercase font-bold"
                )

            # 2. ACTIVE NAREDS
            with ui.column().classes("flex-1 p-6 rounded-2xl card"):
                ui.label("TOTAL WORK ITEMS").classes(
                    "text-slate-400 font-bold text-xs tracking-tighter"
                )
                ui.label(f"{wi_count} ITEMS").classes("text-cyan-400 text-4xl font-black mt-2")
                ui.label(f"{pallet_count} Pallets in Stock").classes(
                    "text-slate-500 text-[10px] mt-4 uppercase font-bold"
                )

            # 3. CRITICAL ALERTS
            alert_color: str = "red" if incident_count > 0 else "teal"
            with ui.column().classes("flex-1 p-6 rounded-2xl card"):
                ui.label("ACTIVE INCIDENTS").classes(
                    "text-slate-400 font-bold text-xs tracking-tighter"
                )
                ui.label(str(incident_count)).classes(
                    f"text-{alert_color}-400 text-4xl font-black mt-2"
                )
                ui.label(
                    "Immediate Action Required" if incident_count > 0 else "Workshop stable"
                ).classes("text-slate-500 text-[10px] mt-4 uppercase font-bold")

        # --- MAIN CONTENT AREA: ACTIVITY & LEADER ---
        with ui.row().classes("w-full gap-6 mt-6"):
            # Left Column: Live Activity Stream
            with ui.column().classes("flex-[2] p-6 rounded-2xl card min-h-[400px]"):
                await ActivityStream(session.get_bind(), self.system_scope).render()

            # Right Column: Cluster State & Leader
            with ui.column().classes("flex-1 gap-6"):
                with ui.column().classes("w-full p-6 rounded-2xl card border border-teal-500/20"):
                    ui.label("CURRENT MASTER").classes(
                        "text-slate-400 font-bold text-xs tracking-tighter mb-4"
                    )
                    leader_node: dict[str, Any] | None = next(
                        (n for n in nodes if n.get("is_leader")), None
                    )
                    leader_id: str = (
                        leader_node.get("node_id", "ELECTION...") if leader_node else "ELECTION..."
                    )

                    with ui.row().classes("items-center gap-3"):
                        ui.icon("stars", color="teal-400", size="32px")
                        with ui.column().classes("gap-0"):
                            ui.label(leader_id).classes("text-xl font-bold text-white font-mono")
                            ui.label("Coordination Lock Owner").classes("text-[10px] text-teal-300")

                with ui.column().classes("w-full p-6 rounded-2xl card"):
                    ui.label("SYSTEM HEALTH").classes(
                        "text-slate-400 font-bold text-xs tracking-tighter mb-4"
                    )
                    ui.label("STORAGE: 84%").classes("text-xs text-slate-300")
                    ui.linear_progress(value=0.84).props("color=emerald")
                    ui.label("MEM: 1.2GB / 4GB").classes("text-xs text-slate-300 mt-4")
                    ui.linear_progress(value=0.3).props("color=cyan")
