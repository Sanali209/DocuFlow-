import base64
from datetime import datetime, date
from typing import Dict, Any, List
from nicegui import ui
from docuflow.features.reports.system import ReportSystem, ReportRegistry
from docuflow.domain.entities.production import ReportTemplate
from sqlmodel import select

class ReportsView:
    """
    Workshop Performance & Analytics dashboard.
    
    Principles:
    - Code as Documentation: Interface reflects the modularity of ReportDataBlocks.
    - Premium Aesthetics: High-fidelity dark mode with focused analytics layout.
    """
    
    # Dashboard Theme constants
    UI_THEME = {
        "page_bg": "w-full h-full p-8 bg-[#020617] gap-6",
        "card_config": "w-full p-6 rounded-2xl bg-slate-900/50 border border-white/5 gap-4",
        "preview_bg": "flex-grow h-full bg-white rounded-xl overflow-hidden shadow-2xl relative",
        "label_step": "text-[10px] font-black text-slate-500 tracking-widest uppercase",
        "btn_preview": "w-full bg-indigo-600 font-bold py-3",
        "btn_export": "w-full bg-emerald-600 font-bold py-3"
    }

    def __init__(self, report_system: ReportSystem):
        self.report_system = report_system
        self.html_preview_slot = None
        self.template_selector = None
        self.report_parameters: Dict[str, Any] = {
            "date_from": date.today().strftime('%Y-%m-%d'),
            "date_to": date.today().strftime('%Y-%m-%d')
        }

    async def render_portal(self):
        """
        Builds the analytics and report generation portal.
        
        Example:
            view = ReportsView(system)
            await view.render_portal()
        """
        with ui.column().classes(self.UI_THEME["page_bg"]):
            self._render_header()

            # Main Layout: Configuration Sidebar (Left) | Visual Preview (Right)
            with ui.row().classes('w-full gap-8 h-full'):
                # 1. Configuration Sidebar
                with ui.column().classes('w-80 gap-6'):
                    self._build_template_picker()
                    self._build_parameter_inputs()
                    
                    # Primary Actions
                    ui.button('REFRESH PREVIEW', icon='visibility', on_click=self.refresh_preview_html).classes(self.UI_THEME["btn_preview"]).props('unelevated rounded')
                    ui.button('EXPORT PDF', icon='picture_as_pdf', on_click=self.download_pdf_document).classes(self.UI_THEME["btn_export"]).props('unelevated rounded')

                # 2. Live Preview Panel
                with ui.column().classes(self.UI_THEME["preview_bg"]):
                    ui.label('LIVE REPORT PREVIEW').classes('absolute top-4 right-4 text-[10px] font-bold text-slate-300 tracking-tighter mix-blend-difference')
                    self.html_preview_slot = ui.html('').classes('w-full h-full p-8 overflow-y-auto')
                    await self.refresh_preview_html()

    def _render_header(self):
        """Render the top branding and help bar."""
        with ui.row().classes('w-full items-center justify-between mb-4'):
            with ui.column().classes('gap-1'):
                ui.label('Workshop Intelligence').classes('text-2xl font-bold text-slate-100 uppercase tracking-tighter')
                ui.label('Data-driven shift summaries and material audit trails').classes('text-xs text-slate-600 uppercase tracking-[0.1em]')
            
            ui.button('Dashboard Docs', icon='help_outline', on_click=lambda: ui.notify('Analytics documentation is being compiled.')).props('flat color=slate-500')

    def _build_template_picker(self):
        """Logic to fetch and display available report layouts."""
        with ui.column().classes(self.UI_THEME["card_config"]):
             ui.label('1. Select Layout').classes(self.UI_THEME["label_step"])
             
             templates = self.report_system.db_session.exec(select(ReportTemplate)).all()
             options = {t.name: f"{t.name.replace('_', ' ').title()}" for t in templates}
             default_val = 'shift_summary' if 'shift_summary' in options else (list(options.keys())[0] if options else None)
             self.template_selector = ui.select(options, label='Template Type', value=default_val).classes('w-full')

    def _build_parameter_inputs(self):
        """Builds inputs for report filtering (dates, IDs, etc)."""
        with ui.column().classes(self.UI_THEME["card_config"]):
             ui.label('2. Filter Period').classes(self.UI_THEME["label_step"])
             
             ui.input('Start Date').props('type=date').bind_value(self.report_parameters, 'date_from').classes('w-full')
             ui.input('End Date').props('type=date').bind_value(self.report_parameters, 'date_to').classes('w-full')

    # --- Analytics Generation Flow ---

    async def refresh_preview_html(self):
        """Renders the HTML version of the report into the UI viewport."""
        if not self.html_preview_slot or not self.template_selector: return
        
        try:
            rendered_html = self.report_system.generate_html_preview(self.template_selector.value, self.report_parameters)
            self.html_preview_slot.content = rendered_html
        except Exception as e:
            # Fallback error UX
            self.html_preview_slot.content = f"""
            <div style="color: #ef4444; padding: 40px; font-family: monospace; background: #fef2f2; border: 1px solid #fee2e2;">
                <h3 style="margin-top: 0;">Reporting Engine Error</h3>
                <p>The template failed to assemble blocks: <b>{str(e)}</b></p>
                <hr style="border-top:1px solid #fee2e2; margin: 20px 0;"/>
                <small>Check if all required ReportDataBlocks are registered.</small>
            </div>
            """
            ui.notify(f"Engine Failure: {e}", color='red')

    async def download_pdf_document(self):
        """Generates the PDF binary and triggers a client-side download."""
        try:
            pdf_bytes = self.report_system.generate_pdf_document(self.template_selector.value, self.report_parameters)
            
            # Encode for browser transmission
            base64_encoded_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"docuflow_report_{self.template_selector.value}_{timestamp}.pdf"
            
            ui.download(f"data:application/pdf;base64,{base64_encoded_pdf}", filename=filename)
            ui.notify(f"Report Generated: {filename}", color='emerald')
        except Exception as e:
            ui.notify(f"PDF Export Failed: {e}", color='red')
