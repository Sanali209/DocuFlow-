import datetime
import json
from collections.abc import Sequence
from typing import Any

from loguru import logger
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    ChatMessageType,
    IncidentLog,
    WorkLog,
    WorkLogType,
)
from docuflow.features.chat.system import ChatSystem
from docuflow.features.reports.system import BlockParam, ReportDataBlock, ReportRegistry
from docuflow.infrastructure.config import Config


class IncidentSystem(BaseSystem):
    """
    Workshop failure tracking and downtime analytics engine.

    Principles:
    - Documentation in Code: Methods include Usage Examples.
    - Self-Explaining: Named constants for failure types.
    """

    # Standard Incident Categories
    TYPE_BREAKDOWN = "BREAKDOWN"
    TYPE_DEFECT = "DEFECT"
    TYPE_SUPPLY = "SUPPLY"
    TYPE_MAINTENANCE = "MAINTENANCE"
    TYPE_OTHER = "OTHER"

    def __init__(
        self, config: Config, session: Session, chat_system: ChatSystem, sdk: Any = None
    ) -> None:
        """
        Initialize the incident tracking system.
        """
        super().__init__(config, session)
        self.chat_system = chat_system
        self.sdk = sdk

    async def report_incident(
        self,
        incident_type: str,
        description: str,
        reported_by: str,
        task_item_id: int | None = None,
        work_item_id: int | None = None,
        assigned_group: str | None = None,
        attachments: list[dict] | None = None,
    ) -> IncidentLog:
        """
        Record a new workshop failure and broadcast a high-priority alert to Chat.
        """
        session: Session = self.db_session

        # 1. Create the persistent log entry
        incident_log: IncidentLog = IncidentLog(
            incident_type=incident_type,
            description=description,
            reported_by=reported_by,
            node_id=self.config.node_id,
            task_item_id=task_item_id,
            work_item_id=work_item_id,
            assigned_group=assigned_group,
            attachments=json.dumps(attachments or []),
            resolved=False,
        )

        session.add(incident_log)
        session.commit()  # Ensure persistent storage
        session.refresh(incident_log)

        # 2. Automatically notify the workshop via ChatSystem dependency
        await self._broadcast_incident_alert(incident_log)

        logger.warning(f"Incident {incident_log.id} reported: {incident_type} by {reported_by}")
        return incident_log

    def assign_incident(self, incident_id: int, group_name: str, author: str) -> None:
        """Assign or reassign an incident to a specific workshop group."""
        session: Session = self.db_session
        incident: IncidentLog | None = session.get(IncidentLog, incident_id)
        if not incident:
            return

        incident.assigned_group = group_name
        session.add(incident)

        # Log assignment
        from docuflow.domain.entities.production import WorkLog, WorkLogType

        log: WorkLog = WorkLog(
            log_type=WorkLogType.INFO,
            message=f"Incident {incident_id} assigned to group: {group_name}",
            author=author,
            node_id=self.config.node_id,
            work_item_id=incident.work_item_id,
        )
        session.add(log)
        session.commit()
        logger.info(f"Incident {incident_id} assigned to {group_name} by {author}")

    async def _broadcast_incident_alert(self, incident: IncidentLog) -> None:
        """
        Internal helper to format and send the ChatMessage alert.
        """
        context_info: str = f" [Task: {incident.task_item_id}]" if incident.task_item_id else ""
        alert_content: str = (
            f"⚡ ИНЦИДЕНТ [{incident.incident_type}]: {incident.description}{context_info}"
        )

        await self.chat_system.send_message(
            author=incident.reported_by,
            content=alert_content,
            message_type=ChatMessageType.INCIDENT,
            ref_task_item_id=incident.task_item_id,
            ref_work_item_id=incident.work_item_id,
        )

    async def resolve_incident(
        self, incident_id: int, resolved_by: str, resolution_note: str
    ) -> None:
        """
        Mark a failure as fixed and calculate total workshop downtime.

        Example:
            system.resolve_incident(
                incident_id=1,
                resolved_by="maintenance",
                resolution_note="Replaced belt",
            )
        """
        session: Session = self.db_session
        incident: IncidentLog | None = session.get(IncidentLog, incident_id)
        if not incident or incident.resolved:
            return

        incident.resolved = True
        incident.resolved_at = datetime.datetime.now()
        incident.resolved_by = resolved_by
        incident.resolution_note = resolution_note

        # Determine total time lost in minutes
        resolved_at: datetime.datetime = incident.resolved_at
        assert resolved_at is not None
        delta_time: datetime.timedelta = resolved_at - incident.created_at
        incident.downtime_minutes = max(0.0, delta_time.total_seconds() / 60.0)

        # Log the fix to the WorkLog for legal/audit purposes
        self._audit_resolution(incident)

        session.add(incident)
        session.commit()
        logger.info(
            f"Incident {incident_id} resolved. Downtime: {incident.downtime_minutes or 0.0:.1f} min"
        )

    def _audit_resolution(self, incident: IncidentLog) -> None:
        """
        Create a persistent WorkLog audit trail for this resolution.
        """
        session: Session = self.db_session
        audit_log: WorkLog = WorkLog(
            log_type=WorkLogType.INFO,
            message=(
                f"Incident {incident.id} ({incident.incident_type}) "
                f"resolved by {incident.resolved_by}. "
                f"Downtime: {incident.downtime_minutes or 0.0:.1f} min."
            ),
            node_id=self.config.node_id,
            work_item_id=incident.work_item_id,
            task_item_id=incident.task_item_id,
        )
        session.add(audit_log)

    # --- Analytics & Reporting Queries (Used by ReportSystem) ---

    def get_summary_stats(self) -> dict[str, float]:
        """Aggregate downtime metrics by incident category."""
        session: Session = self.db_session
        statement = select(IncidentLog).where(
            IncidentLog.resolved.is_(True)  # type: ignore[union-attr]
        )
        resolved_incidents: Sequence[IncidentLog] = session.exec(statement).all()

        stats: dict[str, float] = {}
        incident: IncidentLog
        for incident in resolved_incidents:
            stats[incident.incident_type] = stats.get(incident.incident_type, 0.0) + (
                incident.downtime_minutes or 0.0
            )

        return stats

    def get_active_failures(self, limit: int = 20) -> list[IncidentLog]:
        """Retrieve all currently unresolved workshop failures."""
        session: Session = self.db_session
        statement = (
            select(IncidentLog)
            .where(IncidentLog.resolved.is_(False))  # type: ignore[union-attr]
            .order_by(IncidentLog.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(session.exec(statement).all())

    def get_recent_history(self, limit: int = 20) -> list[IncidentLog]:
        """
        Retrieve a list of recently resolved incidents for audit purposes.

        Example:
            history = system.get_recent_history(limit=5)
        """
        session: Session = self.db_session
        statement = (
            select(IncidentLog)
            .where(IncidentLog.resolved.is_(True))  # type: ignore[union-attr]
            .order_by(IncidentLog.resolved_at.desc())  # type: ignore[union-attr]
            .limit(limit)
        )
        return list(session.exec(statement).all())

    # --- System Startup & Registration ---

    async def on_startup(self) -> None:
        """Lifecycle hook to register reporting blocks in the global registry."""
        if not self.sdk:
            return
        registry: ReportRegistry = await self.sdk.resolve_system_by_type(ReportRegistry)

        registry.register(
            ReportDataBlock(
                name="downtime_summary",
                label="Workshop Downtime (Cumulative)",
                params=[],
                query_fn=lambda db, params: self.get_summary_stats(),
            )
        )

        # Example of registering a block with documentation in code
        registry.register(
            ReportDataBlock(
                name="incident_log",
                label="Historical Incident Log",
                params=[BlockParam("limit", "Rows", "int")],
                query_fn=self._query_historical_log,
            )
        )

    def _query_historical_log(self, db_session: Session, report_params: dict) -> list[dict]:
        """
        Query helper for registration block.
        """
        row_limit: Any = report_params.get("limit", 50)
        if not isinstance(row_limit, int):
            row_limit = 50
        statement = (
            select(IncidentLog)
            .order_by(IncidentLog.created_at.desc())  # type: ignore[attr-defined]
            .limit(row_limit)
        )
        incidents: Sequence[IncidentLog] = db_session.exec(statement).all()
        return [
            {
                "type": incident.incident_type,
                "desc": incident.description,
                "by": incident.reported_by,
                "resolved": incident.resolved,
            }
            for incident in incidents
        ]
