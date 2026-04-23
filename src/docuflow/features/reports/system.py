import datetime
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from jinja2 import BaseLoader, Environment, select_autoescape
from loguru import logger
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import ReportTemplate
from docuflow.infrastructure.config import Config


@dataclass
class BlockParam:
    """Metadata for a report data block parameter (e.g., date_from)."""

    name: str
    label: str
    param_type: str  # "date", "str", "int"


@dataclass
class ReportDataBlock:
    """A modular data query registered by any feature module."""

    name: str
    label: str
    params: list[BlockParam]
    query_fn: Callable[[Session, dict[str, Any]], Any]


class ReportRegistry:
    """
    Global registry for cross-system report data blocks.
    In a distributed cluster, each node maintains its own registry instances.
    """

    def __init__(self):
        self._blocks: dict[str, ReportDataBlock] = {}

    def register(self, block: ReportDataBlock):
        """Add a new queryable data block to the registry."""
        self._blocks[block.name] = block
        logger.debug(f"ReportRegistry: Registered block '{block.name}'")

    def get_block(self, name: str) -> ReportDataBlock | None:
        """Retrieve a block by its system-wide unique name."""
        return self._blocks.get(name)

    def available_blocks(self) -> list[ReportDataBlock]:
        """Returns all registered block definitions for metadata inspection."""
        return list(self._blocks.values())


class BlockProxy:
    """
    A Jinja2 helper that allows calling registered data blocks dynamically in HTML.

    Example:
        {{ blocks.stock_snapshot() }}
    """

    def __init__(
        self, registry: ReportRegistry, db_session: Session, global_params: dict[str, Any]
    ):
        self._registry = registry
        self._db_session = db_session
        self._global_params = global_params

    def __getattr__(self, name: str):
        # Resolve the block from the registry
        block = self._registry.get_block(name)
        if not block:
            raise AttributeError(f"Report Engine: Unknown data block: {name}")

        def _call_query(**kwargs):
            # Combine template-level args with global report params
            merged_params = {**self._global_params, **kwargs}
            return block.query_fn(self._db_session, merged_params)

        return _call_query


class ReportSystem(BaseSystem):
    """
    The workshop analytics and PDF reporting engine.

    Principles:
    - Code as Documentation: Direct Jinja2 interaction via BlockProxy.
    - Performance: WeasyPrint for professional PDF layouts.
    """

    # Internal Template Names
    TEMPLATE_SHIFT_SUMMARY = "shift_summary"
    TEMPLATE_MATERIAL_AUDIT = "material_audit"
    TEMPLATE_INCIDENT_LOG = "incident_log"

    def __init__(self, config: Config, session: Session, registry: ReportRegistry):
        """
        Initialize the reporting engine.

        Args:
            config: System configuration.
            session: SQLModel session for data aggregation.
            registry: Central registry for report data blocks.
        """
        super().__init__(config, session)
        self.registry = registry

    def get_all_templates(self) -> list[ReportTemplate]:
        """Retrieves all registered report templates from the database."""
        return list(self.db_session.exec(select(ReportTemplate)).all())

    def generate_html_preview(self, template_name: str, params: dict[str, Any]) -> str:
        """
        Renders a Jinja2 template into a raw HTML string for previewing.

        Example:
            html = system.generate_html_preview("shift_by_date", {"date_from": "2024-05-01"})
        """
        report_template = self.db_session.exec(
            select(ReportTemplate).where(ReportTemplate.name == template_name)
        ).first()

        if not report_template:
            raise ValueError(f"Report Engine: Template '{template_name}' not found.")

        # Initialize the 'magic' proxy that calls other systems
        proxy = BlockProxy(self.registry, self.db_session, params)
        rendering_context = {
            "blocks": proxy,
            "params": params,
            "current_time": datetime.datetime.now(),
            "node_id": self._config.node_id,
        }

        env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html", "xml"]))
        jinja_template = env.from_string(report_template.template_html)
        return jinja_template.render(**rendering_context)

    def generate_pdf_document(self, template_name: str, params: dict[str, Any]) -> bytes:
        """
        Generates a PDF byte-stream using the WeasyPrint engine.

        Example:
            pdf_bytes = system.generate_pdf_document("material_audit", {})
        """
        html_rendered = self.generate_html_preview(template_name, params)

        try:
            from weasyprint import HTML

            return HTML(string=html_rendered).write_pdf()
        except (ImportError, Exception) as e:
            logger.error(f"Reports: PDF Engine failure ({e}). Falling back to HTML bytes.")
            return html_rendered.encode("utf-8")

    async def on_startup(self):
        """Lifecycle: Seed default factory templates into the cluster DB."""
        await self._seed_factory_templates()

    async def _seed_factory_templates(self):
        """Internal helper to populate the database with default report layouts."""
        factory_names = [
            self.TEMPLATE_SHIFT_SUMMARY,
            self.TEMPLATE_MATERIAL_AUDIT,
            self.TEMPLATE_INCIDENT_LOG,
        ]

        for name in factory_names:
            existing = self.db_session.exec(
                select(ReportTemplate).where(ReportTemplate.name == name)
            ).first()
            if not existing:
                default_template = self._get_factory_template(name)
                if default_template:
                    self.db_session.add(default_template)
        self.db_session.commit()

    def _get_factory_template(self, name: str) -> ReportTemplate | None:
        """Retrieves built-in HTML layouts for initial deployment."""
        TEMPLATES = {
            self.TEMPLATE_SHIFT_SUMMARY: ReportTemplate(
                name=self.TEMPLATE_SHIFT_SUMMARY,
                description="Daily production, downtime, and material audit summary.",
                template_html=self._get_shift_summary_html(),
            ),
            self.TEMPLATE_MATERIAL_AUDIT: ReportTemplate(
                name=self.TEMPLATE_MATERIAL_AUDIT,
                description="Complete history of material movements and write-offs.",
                template_html=self._get_material_audit_html(),
            ),
            self.TEMPLATE_INCIDENT_LOG: ReportTemplate(
                name=self.TEMPLATE_INCIDENT_LOG,
                description="Detailed log of all workshop failures and resolutions.",
                template_html=self._get_incident_log_html(),
            ),
        }
        return TEMPLATES.get(name)

    def _get_shift_summary_html(self) -> str:
        """Modularized HTML template string for shift summaries."""
        return """
        <style>
            body { font-family: 'Inter', sans-serif; color: #334155; line-height: 1.5; padding: 50px; }
            h1 { color: #f43f5e; border-bottom: 3px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 30px; }
            .section { margin-top: 30px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { border: 1px solid #f1f5f9; padding: 12px; text-align: left; }
            th { background: #f8fafc; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; }
        </style>
        <h1>SHIFT PERFORMANCE: {{ node_id }}</h1>
        <p><strong>Generated:</strong> {{ current_time.strftime('%d.%m.%Y %H:%M') }}</p>
        <p><strong>Period:</strong> {{ params.date_from }} to {{ params.date_to }}</p>

        <div class="section">
            <h2>DOWNTIME BY CATEGORY</h2>
            <table>
                <tr><th>Incident Type</th><th>Cumulative Minutes</th></tr>
                {% for category, minutes in blocks.downtime_summary().items() %}
                <tr><td>{{ category }}</td><td>{{ minutes|round(1) }} min</td></tr>
                {% endfor %}
            </table>
        </div>

        <div class="section">
            <h2>INCIDENT LOG</h2>
            {% for entry in blocks.incident_log() %}
            <div style="border-left: 3px solid #f43f5e; padding: 10px 20px; background: #fff1f2; margin-bottom: 10px;">
                <strong>{{ entry.type }}</strong>: {{ entry.desc }} (reported by {{ entry.by }})  # type: ignore[attr-defined]
                <br/><small>Status: {{ 'Resolved' if entry.resolved else 'UNRESOLVED' }}</small>
            </div>
            {% endfor %}
        </div>
        """

    def _get_material_audit_html(self) -> str:
        """HTML template for material traceability reports."""
        return """
        <style>
            body { font-family: 'Inter', sans-serif; color: #334155; padding: 40px; }
            h1 { color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }
            th, td { border: 1px solid #e2e8f0; padding: 10px; text-align: left; }
            th { background: #f8fafc; color: #64748b; text-transform: uppercase; }
            .delta-neg { color: #dc2626; font-weight: bold; }
            .delta-pos { color: #16a34a; font-weight: bold; }
        </style>
        <h1>MATERIAL AUDIT LOG</h1>
        <p>Node: {{ node_id }} | Period: {{ params.date_from }} - {{ params.date_to }}</p>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Operation</th>
                    <th>Delta</th>
                    <th>Author</th>
                    <th>Reason / Context</th>
                </tr>
            </thead>
            <tbody>
                {% for item in blocks.material_usage_audit(limit=100) %}
                <tr>
                    <td>{{ item.date }}</td>
                    <td>{{ item.operation.upper() }}</td>
                    <td class="{{ 'delta-neg' if item.delta < 0 else 'delta-pos' }}">
                        {{ item.delta }}
                    </td>
                    <td>{{ item.author }}</td>
                    <td>{{ item.reason or '—' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        """

    def _get_incident_log_html(self) -> str:
        """HTML template for the historical incident report."""
        return """
        <style>
            body { font-family: 'Inter', sans-serif; color: #334155; padding: 40px; }
            h1 { color: #991b1b; border-bottom: 2px solid #fee2e2; padding-bottom: 10px; }
            .incident-card { border: 1px solid #fca5a5; background: #fff1f2; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
            .meta { font-size: 11px; color: #b91c1c; font-weight: bold; margin-bottom: 5px; }
            .desc { font-size: 14px; margin-bottom: 10px; }  # type: ignore[attr-defined]
            .res { border-top: 1px solid #fecaca; padding-top: 8px; font-size: 12px; color: #15803d; }
        </style>
        <h1>WORKSHOP INCIDENT LOG</h1>
        {% for incident in blocks.incident_log(limit=50) %}
        <div class="incident-card">
            <div class="meta">{{ incident.type }} | Reported by: {{ incident.by }}</div>
            <div class="desc">{{ incident.desc }}</div>  # type: ignore[attr-defined]
            {% if incident.resolved %}
            <div class="res">✓ Resolved: {{ incident.res_note }}</div>
            {% else %}
            <div class="res" style="color: #dc2626;">⚠ UNRESOLVED</div>
            {% endif %}
        </div>
        {% endfor %}
        """
