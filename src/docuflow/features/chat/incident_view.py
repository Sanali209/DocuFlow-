from nicegui import ui
from typing import List, Optional, Dict, Any
from datetime import datetime
from docuflow.features.chat.incidents import IncidentSystem
from docuflow.domain.entities.production import IncidentLog

class IncidentView:
    """
    Workshop incident and downtime monitoring dashboard.
    
    Principles:
    - Code as Documentation: Methods are self-descriptive and documented with examples.
    - Theme Integrity: Shared styling extracted into localized constants.
    """
    
    # UI Theme for the Incident Dashboard
    UI_THEME = {
        "page_bg": "w-full h-full p-8 bg-[#020617] gap-6",
        "card_active": "w-full p-4 rounded-xl border border-red-500/30 bg-red-500/5 items-center gap-4 transition-all hover:bg-red-500/10",
        "card_history": "w-full p-3 rounded border border-emerald-500/10 bg-emerald-500/5 gap-2",
        "label_pill": "text-[10px] font-black tracking-[0.2em] mb-2 uppercase",
        "stat_label": "text-[9px] text-slate-500 tracking-widest uppercase"
    }

    def __init__(self, incident_system: IncidentSystem):
        self.incident_system = incident_system
        self.active_failures_container = None
        self.recent_history_container = None
        self.metrics_summary_container = None

    async def render_dashboard(self):
        """
        Renders the complete workshop failure monitor.
        
        Example:
            incident_dashboard = IncidentView(system)
            await incident_dashboard.render_dashboard()
        """
        with ui.column().classes(self.UI_THEME["page_bg"]):
            self._render_header_section()

            # Main Content Layout: Active (Left) | History (Right)
            with ui.row().classes('w-full gap-6 h-full'):
                # Left Column: Active workshop blockers
                with ui.column().classes('flex-grow flex-col h-full bg-[#020617]'):
                    ui.label('CRITICAL BLOCKERS').classes(f"{self.UI_THEME['label_pill']} text-red-500")
                    self.active_failures_container = ui.column().classes('w-full gap-3')
                    await self.refresh_active_feed()

                # Right Column: Historical context
                with ui.column().classes('w-96 border-l border-white/5 pl-6 h-full gap-6'):
                    ui.label('RECENT RESOLUTIONS').classes(f"{self.UI_THEME['label_pill']} text-emerald-500")
                    self.recent_history_container = ui.column().classes('w-full gap-3 overflow-y-auto max-h-[60vh]')
                    await self.refresh_history_feed()

            await self.refresh_metrics_summary()

    def _render_header_section(self):
        """Builds the top bar with title, metrics slot, and actions."""
        with ui.row().classes('w-full items-center justify-between mb-2'):
            with ui.column().classes('gap-1'):
                ui.label('Workshop Integrity').classes('text-2xl font-bold text-slate-100 uppercase tracking-tighter')
                ui.label('Monitoring real-time failures and resolution velocity').classes('text-xs text-slate-600 uppercase tracking-[0.1em]')
            
            with ui.row().classes('gap-4'):
                self.metrics_summary_container = ui.row().classes('gap-4')
                ui.button('Report Breakdown', icon='report_problem', on_click=self.open_reporting_dialog).classes('bg-red-600 font-bold px-6 py-2').props('unelevated rounded')
                ui.button(icon='refresh', on_click=self.full_refresh).props('flat round size=sm color=slate-500')

    # --- Data Lifecycle & Rerendering ---

    async def full_refresh(self):
        """Complete UI data resync."""
        await self.refresh_active_feed()
        await self.refresh_history_feed()
        await self.refresh_metrics_summary()

    async def refresh_active_feed(self):
        """Reload the list of unresolved failures."""
        if not self.active_failures_container: return
        self.active_failures_container.clear()
        
        active_list = self.incident_system.get_active_failures()
        
        if not active_list:
             with self.active_failures_container:
                  ui.label('No active blockers detected.').classes('text-slate-600 text-sm mt-10 italic')
             return

        for incident in active_list:
             self._render_active_incident_card(incident)

    async def refresh_history_feed(self):
        """Reload the list of recently resolved failures."""
        if not self.recent_history_container: return
        self.recent_history_container.clear()
        
        resolution_history = self.incident_system.get_recent_history()
        
        for incident in resolution_history:
            with self.recent_history_container:
                with ui.row().classes(self.UI_THEME["card_history"]):
                    ui.icon('check_circle', color='emerald', size='14px').classes('mt-1')
                    with ui.column().classes('flex-grow gap-0'):
                        ui.label(incident.incident_type).classes('text-[10px] font-bold text-emerald-400 uppercase tracking-widest')
                        ui.label(incident.description).classes('text-xs text-slate-300 line-clamp-1')
                        ui.label(f"{incident.downtime_minutes:.0f} min lost").classes('text-[9px] text-slate-600 mt-1 font-mono')

    async def refresh_metrics_summary(self):
        """Updates the high-level metrics counters in the header."""
        if not self.metrics_summary_container: return
        self.metrics_summary_container.clear()
        
        stats_map = self.incident_system.get_summary_stats()
        total_downtime_minutes = sum(stats_map.values())
        active_blockers_count = len(self.incident_system.get_active_failures())
        
        with self.metrics_summary_container:
             # Critical Count
             with ui.column().classes('items-end justify-center'):
                  ui.label(str(active_blockers_count)).classes(f'text-3xl font-black {"text-red-500" if active_blockers_count > 0 else "text-slate-800"}')
                  ui.label('ACTIVE').classes(self.UI_THEME["stat_label"])
             # Cumulative Downtime
             with ui.column().classes('items-end justify-center ml-4'):
                  ui.label(f"{total_downtime_minutes / 60:.1f}h").classes('text-2xl font-mono text-emerald-500')
                  ui.label('DOWNTIME').classes(self.UI_THEME["stat_label"])

    def _render_active_incident_card(self, incident: IncidentLog):
        """Render a single actionable card for a workshop breakdown."""
        with self.active_failures_container:
            with ui.row().classes(self.UI_THEME["card_active"]):
                ui.icon('warning', color='red-500', size='24px')
                with ui.column().classes('flex-grow gap-1'):
                    with ui.row().classes('items-center gap-2'):
                         ui.label(incident.incident_type).classes('text-[9px] font-black px-2 py-0.5 rounded bg-red-500/20 text-red-100 uppercase')
                         ui.label(f"FAILURE-ID: {incident.id}").classes('text-[9px] font-mono text-slate-700')
                    
                    ui.label(incident.description).classes('text-sm text-slate-200 mt-1 font-medium')
                    
                    with ui.row().classes('text-[10px] text-slate-600 gap-3 mt-2'):
                         ui.label(f"Reported: {incident.created_at.strftime('%H:%M')}")
                         if incident.task_item_id:
                              ui.label(f"Task: {incident.task_item_id}")

                ui.button('Resolve', icon='done_all', on_click=lambda: self.open_resolution_dialog(incident)).classes('bg-emerald-600/20 text-emerald-400 font-bold px-4').props('flat rounded size=sm')

    # --- Interaction Handlers ---

    def open_resolution_dialog(self, incident: IncidentLog):
        """Dialog to close a failure log and record its fix."""
        with ui.dialog() as dialog, ui.card().classes('bg-slate-900 border border-emerald-500/20 w-96 p-6'):
             ui.label('RESOLVE FAILURE').classes('text-sm font-black text-emerald-400 mb-4 tracking-widest')
             
             note = ui.textarea(label='Resolution Note', placeholder='Replaced motor / Repaired leak...').classes('w-full')
             tech_name = ui.input(label='Technician ID').classes('w-full').props('value="maintenance-01"')
             
             async def submit():
                  if not note.value: return
                  self.incident_system.resolve_incident(incident.id, tech_name.value, note.value)
                  dialog.close()
                  await self.full_refresh()
                  ui.notify(f"Incident {incident.id} cleared.", color='emerald')

             with ui.row().classes('w-full justify-end mt-6'):
                  ui.button('Cancel', on_click=dialog.close).props('flat text-color=slate-500')
                  ui.button('CONFIRM FIX', on_click=submit).props('unelevated color=emerald')
        dialog.open()

    def open_reporting_dialog(self):
        """Manual reporting interface for workshop operators."""
        with ui.dialog() as dialog, ui.card().classes('bg-slate-900 border border-red-500/20 w-96 p-6'):
             ui.label('REPORT FAILURE').classes('text-sm font-black text-red-500 mb-4 tracking-widest')
             
             # Use systemic constants for type selection
             opts = [self.incident_system.TYPE_BREAKDOWN, self.incident_system.TYPE_DEFECT, self.incident_system.TYPE_SUPPLY]
             type_select = ui.select(opts, label='Failure Category').classes('w-full')
             desc = ui.textarea(label='Issue Description').classes('w-full')
             
             async def submit():
                  if not type_select.value or not desc.value: return
                  self.incident_system.report_incident(type_select.value, desc.value, "workshop-op")
                  dialog.close()
                  await self.full_refresh()
                  ui.notify('Failure logged and broadcasted', color='red')

             with ui.row().classes('w-full justify-end mt-6'):
                  ui.button('Cancel', on_click=dialog.close).props('flat text-color=slate-500')
                  ui.button('PRIORITY BROADCAST', on_click=submit).props('unelevated color=red')
        dialog.open()
