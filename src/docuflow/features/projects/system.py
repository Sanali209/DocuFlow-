import datetime

from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import Project, WorkItem, WorkLog, WorkLogType
from docuflow.infrastructure.config import Config


class ProjectSystem(BaseSystem):
    """
    Manages high-level project grouping and WorkItem logistics.

    Principles:
    - Default Fallback: Ensures a 'Default' project exists for unassigned ingestions.
    - Reassignment Traceability: Every move between projects is logged in the WorkLog.
    - Code as Documentation: Methods are self-describing and include examples.
    """

    def __init__(self, config: Config, db_session: Session):
        super().__init__(config, db_session)

    def get_all_active_projects(self) -> list[Project]:
        """
        Lists all projects currently registered in the database.
        """
        return list(self.db_session.exec(select(Project)).all())

    def register_new_project(self, project_name: str, description: str | None = None) -> Project:
        """
        Creates a new production folder representing a specific client or internal project.

        Example:
            project = system.register_new_project(project_name="IKEA-2026", description="Living room series")
        """
        new_project = Project(name=project_name, description=description)
        self.db_session.add(new_project)
        self.db_session.flush()
        self.db_session.refresh(new_project)
        return new_project

    def reassign_production_group(self, work_item_id: int, target_project_id: int) -> WorkItem:
        """
        Moves a WorkItem (production folder) to a different project grouping for better organization.

        Example:
            updated_item = system.reassign_production_group(work_item_id=10, target_project_id=2)
        """
        work_item = self.db_session.get(WorkItem, work_item_id)
        if not work_item:
            raise ValueError(f"Project Engine: WorkItem {work_item_id} not found.")

        target_project = self.db_session.get(Project, target_project_id)
        if not target_project:
            raise ValueError(f"Project Engine: Target project {target_project_id} not registered.")

        previous_project_id = work_item.project_id
        work_item.project_id = target_project_id

        # Log the relocation for audit purposes
        log_entry = WorkLog(
            work_item_id=work_item.id,
            log_type=WorkLogType.STATUS_CHANGE.value,
            message=f"Workshop: Reassigned from Project ID {previous_project_id} to '{target_project.name}'",
            node_id=self.config.node_id,
            created_at=datetime.datetime.now(),
        )
        self.db_session.add(log_entry)
        self.db_session.add(work_item)
        self.db_session.flush()
        self.db_session.refresh(work_item)
        return work_item

    def resolve_default_workshop_project(self) -> Project:
        """
        Retrieves the global 'Default' project or creates it if missing.
        Required for automatic folder scanning fallback mechanisms.
        """
        default_project = self.db_session.exec(
            select(Project).where(Project.name == "Default")
        ).first()

        if not default_project:
            default_project = Project(name="Default", is_default=True)
            self.db_session.add(default_project)
            self.db_session.flush()
            self.db_session.refresh(default_project)

        return default_project
