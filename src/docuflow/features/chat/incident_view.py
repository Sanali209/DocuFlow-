from collections.abc import Callable
from typing import Any, ClassVar

from nicegui import ui

from docuflow.domain.entities.production import IncidentLog
from docuflow.features.chat.incidents import IncidentSystem
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper


def register_incidents_view():
    """Register the workshop incidents dashboard."""
    ViewRegistry.register(
        ViewInfo(
            name="incidents",
            label="Incidents",
            icon="report_problem",
            render_fn=incidents_view_wrapper,
            dependencies=[IncidentSystem],
            pass_user=True,
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def incidents_view_wrapper(
    system: IncidentSystem, user: str, system_scope: Callable, layout: Any
):
    """Wrapper to instantiate and render the IncidentView."""
    view = IncidentView(system, current_user=user, system_scope=system_scope, layout=layout)
    await view.render_dashboard()


class IncidentView(BaseDocuWidget):
    """
    Workshop incident and downtime monitoring dashboard.
    """

    # UI Theme for the Incident Dashboard
    UI_THEME: ClassVar[dict[str, str]] = {
        "page_bg": "w-full h-full p-8 bg-[#020617] gap-6",
        "card_active": "w-full p-4 rounded-xl border border-red-500/30 bg-red-500/5 items-center gap-4 transition-all hover:bg-red-500/10",
        "card_history": "w-full p-3 rounded border border-emerald-500/10 bg-emerald-500/5 gap-2",
        "label_pill": "text-[10px] font-black tracking-[0.2em] mb-2 uppercase",
        "stat_label": "text-[9px] text-slate-500 tracking-widest uppercase",
    }

    def __init__(
        self,
        incident_system: IncidentSystem,
        current_user: str = "foreman",
        system_scope: Callable | None = None,
        layout: Any = None,
    ):
        super().__init__(system_scope)
        self.incident_system = incident_system
        self.current_user = current_user
        self.layout = layout
        self.active_failures_container: Any = None
        self.recent_history_container: Any = None
        self.metrics_summary_container: Any = None
        self.active_group_filter = "ALL"

    async def render_dashboard(self):
        """
        Renders the complete workshop failure monitor.
        """
        with ui.column().classes(self.UI_THEME["page_bg"]):
            self._render_header_section()

            # Group Filter Tabs
            self._render_group_tabs()

            # Main Content Layout: Active (Left) | History (Right)
            with ui.row().classes("w-full gap-6 h-full"):
                # Left Column: Active workshop blockers
                with ui.column().classes("flex-grow flex-col h-full bg-[#020617]"):
                    ui.label("CRITICAL BLOCKERS").classes(
                        f"{self.UI_THEME['label_pill']} text-red-500"
                    )
                    self.active_failures_container = ui.column().classes("w-full gap-3")
                    await self.refresh_active_feed()

                # Right Column: Historical context
                with ui.column().classes("w-96 border-l border-white/5 pl-6 h-full gap-6"):
                    ui.label("RECENT RESOLUTIONS").classes(
                        f"{self.UI_THEME['label_pill']} text-emerald-500"
                    )
                    self.recent_history_container = ui.column().classes(
                        "w-full gap-3 overflow-y-auto max-h-[60vh]"
                    )
                    await self.refresh_history_feed()

            await self.refresh_metrics_summary()

            # Live updates every 10 seconds
            if self.layout:
                self.layout.register_timer(ui.timer(10.0, self.full_refresh))
            else:
                ui.timer(10.0, self.full_refresh)

    def _render_group_tabs(self):
        """Renders filtering tabs by responsible group."""
        groups = ["ALL", "Foreman", "Maintenance", "Supply", "IT"]
        with ui.tabs().classes("w-full text-indigo-400 bg-white/5 rounded-xl") as tabs:
            for g in groups:
                ui.tab(g)

        tabs.on("change", lambda e: self._filter_by_group(e.value))

    async def _filter_by_group(self, group_name: str):
        self.active_group_filter = group_name
        await self.refresh_active_feed()

    def _render_header_section(self):
        """Builds the top bar with title, metrics slot, and actions."""
        with ui.row().classes("w-full items-center justify-between mb-2"):
            with ui.column().classes("gap-1"):
                ui.label("Workshop Integrity").classes(
                    "text-2xl font-bold text-slate-100 uppercase tracking-tighter"
                )
                ui.label("Monitoring real-time failures and resolution velocity").classes(
                    "text-xs text-slate-600 uppercase tracking-[0.1em]"
                )

            with ui.row().classes("gap-4"):
                self.metrics_summary_container = ui.row().classes("gap-4")
                ui.button(
                    "Report Breakdown", icon="report_problem", on_click=self.open_reporting_dialog
                ).classes("bg-red-600 font-bold px-6 py-2").props("unelevated rounded")
                ui.button(icon="refresh", on_click=self.full_refresh).props(
                    "flat round size=sm color=slate-500"
                )

    # --- Data Lifecycle & Rerendering ---

    async def full_refresh(self):
        """Complete UI data resync."""
        await self.refresh_active_feed()
        await self.refresh_history_feed()
        await self.refresh_metrics_summary()

    async def refresh_active_feed(self):
        """Reload the list of unresolved failures."""
        if not self.active_failures_container:
            return
        self.active_failures_container.clear()

        async with self.scope() as req:
            fresh_incident_sys = await req.get(IncidentSystem)
            active_list = fresh_incident_sys.get_active_failures()

            if not active_list:
                with self.active_failures_container:
                    ui.label("No active blockers detected.").classes(
                        "text-slate-600 text-sm mt-10 italic"
                    )
                return

            for incident in active_list:
                self._render_active_incident_card(incident)

    async def refresh_history_feed(self):
        """Reload the list of recently resolved failures."""
        if not self.recent_history_container:
            return
        self.recent_history_container.clear()

        async with self.scope() as req:
            fresh_incident_sys = await req.get(IncidentSystem)
            resolution_history = fresh_incident_sys.get_recent_history()

            for incident in resolution_history:
                with self.recent_history_container:
                    with ui.row().classes(self.UI_THEME["card_history"]):
                        ui.icon("check_circle", color="emerald", size="14px").classes("mt-1")
                        with ui.column().classes("flex-grow gap-0"):
                            ui.label(incident.incident_type).classes(
                                "text-[10px] font-bold text-emerald-400 uppercase tracking-widest"
                            )
                            ui.label(incident.description).classes(
                                "text-xs text-slate-300 line-clamp-1"
                            )
                            ui.label(f"{incident.downtime_minutes:.0f} min lost").classes(
                                "text-[9px] text-slate-600 mt-1 font-mono"
                            )

    async def refresh_metrics_summary(self):
        """Updates the high-level metrics counters in the header."""
        if not self.metrics_summary_container:
            return
        self.metrics_summary_container.clear()

        async with self.scope() as req:
            fresh_incident_sys = await req.get(IncidentSystem)
            stats_map = fresh_incident_sys.get_summary_stats()
            total_downtime_minutes = sum(stats_map.values())
            active_blockers_count = len(fresh_incident_sys.get_active_failures())

            with self.metrics_summary_container:
                # Critical Count
                with ui.column().classes("items-end justify-center"):
                    ui.label(str(active_blockers_count)).classes(
                        f"text-3xl font-black {'text-red-500' if active_blockers_count > 0 else 'text-slate-800'}"
                    )
                    ui.label("ACTIVE").classes(self.UI_THEME["stat_label"])
                # Cumulative Downtime
                with ui.column().classes("items-end justify-center ml-4"):
                    ui.label(f"{total_downtime_minutes / 60:.1f}h").classes(
                        "text-2xl font-mono text-emerald-500"
                    )
                    ui.label("DOWNTIME").classes(self.UI_THEME["stat_label"])

    def open_reporting_dialog(self):
        """Manual reporting interface for workshop operators."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("bg-slate-900 border border-red-500/20 w-96 p-6"),
        ):
            ui.label("REPORT FAILURE").classes(
                "text-sm font-black text-red-500 mb-4 tracking-widest"
            )

            # Use systemic constants for type selection
            opts = [
                self.incident_system.TYPE_BREAKDOWN,
                self.incident_system.TYPE_DEFECT,
                self.incident_system.TYPE_SUPPLY,
            ]
            type_select = ui.select(opts, label="Failure Category").classes("w-full")
            desc = ui.textarea(label="Issue Description").classes("w-full")

            async def submit():
                if not type_select.value or not desc.value:
                    return
                async with self.scope() as req:
                    fresh_incident_sys = await req.get(IncidentSystem)
                    await fresh_incident_sys.report_incident(
                        type_select.value, desc.value, self.current_user
                    )
                dialog.close()
                await self.full_refresh()
                NotifyHelper.error("Failure logged and broadcasted")

            with ui.row().classes("w-full justify-end mt-6"):
                ui.button("Cancel", on_click=dialog.close).props("flat text-color=slate-500")
                ui.button("PRIORITY BROADCAST", on_click=submit).props("unelevated color=red")
        dialog.open()

    def _render_active_incident_card(self, incident: IncidentLog):
        """Render a single actionable card for a workshop breakdown."""
        # Filter logic
        if (
            self.active_group_filter != "ALL"
            and incident.assigned_group != self.active_group_filter
        ):
            return

        with self.active_failures_container:
            with ui.row().classes(self.UI_THEME["card_active"]):
                ui.icon("warning", color="red-500", size="24px")
                with ui.column().classes("flex-grow gap-1"):
                    with ui.row().classes("items-center gap-2"):
                        ui.label(incident.incident_type).classes(
                            "text-[9px] font-black px-2 py-0.5 rounded bg-red-500/20 text-red-100 uppercase"
                        )
                        if incident.assigned_group:
                            ui.badge(f"➔ {incident.assigned_group}").props(
                                "color=indigo-600 size=xs"
                            )

                        ui.label(f"FAILURE-ID: {incident.id}").classes(
                            "text-[9px] font-mono text-slate-700"
                        )

                    ui.label(incident.description).classes(
                        "text-sm text-slate-200 mt-1 font-medium"
                    )

                    with ui.row().classes("text-[10px] text-slate-600 gap-3 mt-2"):
                        ui.label(f"Reported: {incident.created_at.strftime('%H:%M')}")
                        if incident.task_item_id:
                            ui.label(f"Task: {incident.task_item_id}")

                with ui.row().classes("gap-2"):
                    # Quick assign to current user's role/group if IT/Maintenance
                    if not incident.assigned_group:
                        ui.button(
                            "Claim",
                            icon="pan_tool",
                            on_click=lambda i=incident: self._claim_incident(i),
                        ).classes("bg-blue-600/20 text-blue-400 font-bold px-4").props(
                            "flat rounded size=sm"
                        )

                    ui.button(
                        "Resolve",
                        icon="done_all",
                        on_click=lambda i=incident: self.open_resolution_dialog(i),
                    ).classes("bg-emerald-600/20 text-emerald-400 font-bold px-4").props(
                        "flat rounded size=sm"
                    )

    async def _claim_incident(self, incident: IncidentLog):
        """Assign incident to Maintenance by default when claiming."""
        async with self.scope() as req:
            fresh_incident_sys = await req.get(IncidentSystem)
            fresh_incident_sys.assign_incident(incident.id, "Maintenance", self.current_user)
        NotifyHelper.info(f"Incident {incident.id} assigned to Maintenance")
        await self.refresh_active_feed()

    # --- Interaction Handlers ---

    def open_resolution_dialog(self, incident: IncidentLog):
        """Dialog to close a failure log and record its fix."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("bg-slate-900 border border-emerald-500/20 w-96 p-6"),
        ):
            ui.label("RESOLVE FAILURE").classes(
                "text-sm font-black text-emerald-400 mb-4 tracking-widest"
            )

            note = ui.textarea(
                label="Resolution Note", placeholder="Replaced motor / Repaired leak..."
            ).classes("w-full")
            tech_name = (
                ui.input(label="Technician ID")
                .classes("w-full")
                .props(f'value="{self.current_user}"')
            )

            async def submit():
                if not note.value:
                    return
                async with self.scope() as req:
                    fresh_incident_sys = await req.get(IncidentSystem)
                    await fresh_incident_sys.resolve_incident(
                        incident.id, tech_name.value, note.value
                    )
                dialog.close()
                await self.full_refresh()
                NotifyHelper.info(f"Incident {incident.id} cleared.")

            with ui.row().classes("w-full justify-end mt-6"):
                ui.button("Cancel", on_click=dialog.close).props("flat text-color=slate-500")
                ui.button("CONFIRM FIX", on_click=submit).props("unelevated color=emerald")
        dialog.open()
