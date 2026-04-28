from typing import Any

from sqlmodel import Session, func, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    IncidentLog,
    ProductionUnit,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
    WorkItem,
)
from docuflow.infrastructure.config import Config


class AnalyticsSystem(BaseSystem):
    """
    High-level analytics engine for workshop performance monitoring.
    """

    def __init__(self, config: Config, session: Session):
        super().__init__(config, session)

    def get_cluster_overview_metrics(self) -> dict[str, Any]:
        """
        Calculates basic metrics for the main cluster dashboard.
        """
        session = self.session

        wi_count = session.exec(select(func.count(WorkItem.id))).one()
        incident_count = session.exec(
            select(func.count(IncidentLog.id)).where(IncidentLog.resolved.is_(False))
        ).one()
        pallet_count = session.exec(
            select(func.count(ProductionUnit.id)).where(ProductionUnit.is_stock.is_(True))
        ).one()

        return {
            "work_item_count": wi_count,
            "incident_count": incident_count,
            "stock_pallet_count": pallet_count,
        }

    def get_dashboard_metrics(self) -> dict[str, Any]:
        """
        Calculates key performance indicators for the main analytics dashboard.
        """
        session = self.session

        # 1. Volume Metrics
        total_work_items = session.exec(select(func.count(WorkItem.id))).one()
        total_tasks = session.exec(select(func.count(TaskItem.id))).one()
        completed_tasks = session.exec(
            select(func.count(TaskItem.id)).where(TaskItem.status == TaskItemStatus.DONE)
        ).one()
        total_pallets = session.exec(select(func.count(ProductionUnit.id))).one()
        total_parts_produced = (
            session.exec(select(func.sum(ProductionUnit.qty_produced))).one() or 0
        )

        # 2. Performance Metrics (Drift)
        stmt_drift = select(TaskItem).where(TaskItem.status == TaskItemStatus.DONE)
        done_tasks = session.exec(stmt_drift).all()

        total_drift = 0.0
        count_drift = 0
        for t in done_tasks:
            if t.estimated_minutes and t.actual_minutes:
                # Drift = (Actual - Estimated) / Estimated
                drift_pct = (t.actual_minutes - t.estimated_minutes) / t.estimated_minutes * 100
                total_drift += drift_pct
                count_drift += 1

        avg_drift = round(total_drift / count_drift, 1) if count_drift > 0 else 0.0
        completion_rate = round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0.0

        # 3. Task Status Distribution
        status_counts = {}
        for s in TaskItemStatus:
            count = session.exec(select(func.count(TaskItem.id)).where(TaskItem.status == s)).one()
            if count > 0:
                status_counts[s.value.upper()] = count

        # 4. Task Group Metrics
        total_task_groups = session.exec(select(func.count(TaskGroup.id))).one() or 0

        groups_by_status: dict[str, int] = {}
        for group in session.exec(select(TaskGroup)).all():
            statuses = {t.status for t in group.tasks}
            if TaskItemStatus.IN_PROGRESS in statuses:
                status = "in_progress"
            elif statuses == {TaskItemStatus.DONE}:
                status = "done"
            elif statuses == {TaskItemStatus.PLANNED}:
                status = "planned"
            else:
                status = "mixed"
            groups_by_status[status] = groups_by_status.get(status, 0) + 1

        # 5. Node Utilization
        node_utilization: dict[str, dict[str, int]] = {}
        node_rows = session.exec(
            select(TaskItem.assigned_to_node, TaskItem.status, func.count(TaskItem.id))
            .where(TaskItem.assigned_to_node.isnot(None))
            .group_by(TaskItem.assigned_to_node, TaskItem.status)
        ).all()
        for node, status, count in node_rows:
            node_utilization.setdefault(node, {"active": 0, "queued": 0, "done": 0})
            if status == TaskItemStatus.IN_PROGRESS:
                node_utilization[node]["active"] = count
            elif status == TaskItemStatus.PLANNED:
                node_utilization[node]["queued"] = count
            elif status == TaskItemStatus.DONE:
                node_utilization[node]["done"] = count

        return {
            "total_work_items": total_work_items,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "total_pallets": total_pallets,
            "total_parts_produced": total_parts_produced,
            "avg_drift": avg_drift,
            "count_drift": count_drift,
            "completion_rate": completion_rate,
            "status_counts": status_counts,
            "total_task_groups": total_task_groups,
            "groups_by_status": groups_by_status,
            "node_utilization": node_utilization,
        }
