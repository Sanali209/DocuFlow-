from collections.abc import Callable
from typing import Any

from nicegui import ui
from sqlmodel import Session, func, select

from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.domain.entities.production import IncidentLog, ProductionUnit, WorkItem
from docuflow.features.admin.system import AdminSystem
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.lib.widgets.activity_stream import ActivityStream


def register_dashboard_view():
    """Register the dashboard view in the global registry."""
    ViewRegistry.register(
        ViewInfo(
            name="dashboard",
            label="Dashboard",
            icon="dashboard",
            render_fn=dashboard_view,
            dependencies=[P2POrchestrator, AdminSystem],
            pass_system_provider=True,
            is_async=True,
        )
    )


async def dashboard_view(
    orchestrator: P2POrchestrator, admin_system: AdminSystem, system_provider: Callable, layout: Any
):
    """Providing the centralized cluster overview and health summary."""

    # 0. FETCH DATA
    # Use fresh system for data fetch to avoid DetachedInstance if render is delayed
    fresh_admin = await system_provider(AdminSystem)
    nodes = fresh_admin.get_cluster_nodes()
    db_engine = fresh_admin.session.get_bind()

    with Session(db_engine) as session:
        wi_count = session.exec(select(func.count(WorkItem.id))).one()
        incident_count = session.exec(
            select(func.count(IncidentLog.id)).where(IncidentLog.resolved == False)
        ).one()
        pallet_count = session.exec(
            select(func.count(ProductionUnit.id)).where(ProductionUnit.is_stock == True)
        ).one()

    ui.label("Cluster Management Hub").classes("text-3xl font-bold text-white mb-4")

    # --- TOP KPI ROW ---
    with ui.row().classes("w-full gap-6"):
        # 1. PEER COUNT
        with ui.column().classes("flex-1 p-6 rounded-2xl glass-card relative overflow-hidden"):
            ui.element("div").classes(
                "absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl"
            )
            ui.label("CLUSTERS NODES").classes("text-slate-500 font-bold text-xs tracking-tighter")
            ui.label(f"{len(nodes)} ONLINE").classes("text-emerald-400 text-4xl font-black mt-2")
            ui.label("P2P Mesh Synchronized").classes(
                "text-slate-500 text-[10px] mt-4 uppercase font-bold"
            )

        # 2. ACTIVE NAREDS
        with ui.column().classes("flex-1 p-6 rounded-2xl glass-card relative overflow-hidden"):
            ui.element("div").classes(
                "absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl"
            )
            ui.label("TOTAL WORK ITEMS").classes(
                "text-slate-500 font-bold text-xs tracking-tighter"
            )
            ui.label(f"{wi_count} ITEMS").classes("text-blue-400 text-4xl font-black mt-2")
            ui.label(f"{pallet_count} Pallets in Stock").classes(
                "text-slate-500 text-[10px] mt-4 uppercase font-bold"
            )

        # 3. CRITICAL ALERTS
        alert_color = "red" if incident_count > 0 else "indigo"
        with ui.column().classes("flex-1 p-6 rounded-2xl glass-card relative overflow-hidden"):
            ui.element("div").classes(
                f"absolute top-0 right-0 w-32 h-32 bg-{alert_color}-500/10 rounded-full blur-3xl"
            )
            ui.label("ACTIVE INCIDENTS").classes(
                "text-slate-500 font-bold text-xs tracking-tighter"
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
        with ui.column().classes("flex-[2] p-6 rounded-2xl glass-card min-h-[400px]"):
            ActivityStream.render(ActivityStream(db_engine, system_provider))

        # Right Column: Cluster State & Leader
        with ui.column().classes("flex-1 gap-6"):
            with ui.column().classes(
                "w-full p-6 rounded-2xl glass-card border border-indigo-500/20"
            ):
                ui.label("CURRENT MASTER").classes(
                    "text-slate-500 font-bold text-xs tracking-tighter mb-4"
                )
                leader_node = next((n for n in nodes if n.get("is_leader")), None)
                leader_id = (
                    leader_node.get("node_id", "ELECTION...") if leader_node else "ELECTION..."
                )

                with ui.row().classes("items-center gap-3"):
                    ui.icon("stars", color="indigo-400", size="32px")
                    with ui.column().classes("gap-0"):
                        ui.label(leader_id).classes("text-xl font-bold text-white font-mono")
                        ui.label("Coordination Lock Owner").classes("text-[10px] text-indigo-300")

            with ui.column().classes("w-full p-6 rounded-2xl glass-card opacity-50"):
                ui.label("SYSTEM HEALTH").classes(
                    "text-slate-500 font-bold text-xs tracking-tighter mb-4"
                )
                ui.label("STORAGE: 84%").classes("text-xs text-white")
                ui.linear_progress(value=0.84).props("color=emerald")
                ui.label("MEM: 1.2GB / 4GB").classes("text-xs text-white mt-4")
                ui.linear_progress(value=0.3).props("color=blue")
