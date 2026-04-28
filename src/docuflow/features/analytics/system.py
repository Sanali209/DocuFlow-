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
        session = self.db_session

        wi_count = session.exec(select(func.count(WorkItem.id))).one()  # type: ignore[arg-type]
        incident_count = session.exec(
            select(func.count(IncidentLog.id)).where(IncidentLog.resolved.is_(False))  # type: ignore[attr-defined]
        ).one()  # type: ignore[arg-type]
        pallet_count = session.exec(
            select(func.count(ProductionUnit.id)).where(ProductionUnit.is_stock.is_(True))  # type: ignore[attr-defined]
        ).one()  # type: ignore[arg-type]

        return {
            "work_item_count": wi_count,
            "incident_count": incident_count,
            "stock_pallet_count": pallet_count,
        }

    def get_dashboard_metrics(self) -> dict[str, Any]:
        """
        Calculates key performance indicators for the main analytics dashboard.
        """
        session = self.db_session

        # 1. Volume Metrics
        total_work_items = session.exec(select(func.count(WorkItem.id))).one()  # type: ignore[arg-type]
        total_tasks = session.exec(select(func.count(TaskItem.id))).one()  # type: ignore[arg-type]
        completed_tasks = session.exec(
            select(func.count(TaskItem.id)).where(TaskItem.status == TaskItemStatus.DONE)  # type: ignore[arg-type]
        ).one()  # type: ignore[arg-type]
        total_pallets = session.exec(select(func.count(ProductionUnit.id))).one()  # type: ignore[arg-type]
        total_parts_produced = (
            session.exec(select(func.sum(ProductionUnit.qty_produced))).one() or 0  # type: ignore[arg-type]
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
            count = session.exec(select(func.count(TaskItem.id)).where(TaskItem.status == s)).one()  # type: ignore[arg-type]
            if count > 0:
                status_counts[s.value.upper()] = count

        # 4. Task Group Metrics
        total_task_groups = session.exec(select(func.count(TaskGroup.id))).one() or 0  # type: ignore[arg-type]

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
            select(TaskItem.assigned_to_node, TaskItem.status, func.count(TaskItem.id))  # type: ignore[arg-type]
            .where(TaskItem.assigned_to_node.isnot(None))  # type: ignore[attr-defined]
            .group_by(TaskItem.assigned_to_node, TaskItem.status)
        ).all()
        for node, status, count in node_rows:
            if node is None:
                continue
            node_utilization.setdefault(node, {"active": 0, "queued": 0, "done": 0})
            if status == TaskItemStatus.IN_PROGRESS:
                node_utilization[node]["active"] = count
            elif status == TaskItemStatus.PLANNED:
                node_utilization[node]["queued"] = count
            elif status == TaskItemStatus.DONE:
                node_utilization[node]["done"] = count

        # 6. Pallets by Project
        pallet_by_project: dict[str, int] = {}
        project_pallets = session.exec(
            select(WorkItem.project_id, func.count(ProductionUnit.id))  # type: ignore[arg-type]
            .join(TaskItem, WorkItem.id == TaskItem.work_item_id)  # type: ignore[arg-type]
            .join(ProductionUnit, TaskItem.id == ProductionUnit.task_item_id)  # type: ignore[arg-type]
            .group_by(WorkItem.project_id)  # type: ignore[arg-type]
        ).all()  # type: ignore[arg-type]
        for proj_id, count in project_pallets:
            if proj_id is not None:
                from docuflow.domain.entities.production import Project

                proj = session.get(Project, proj_id)
                name = proj.name if proj else f"Project-{proj_id}"
                pallet_by_project[name] = count

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
            "pallet_by_project": pallet_by_project,
        }
