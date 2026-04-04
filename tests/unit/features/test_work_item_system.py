import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    Project, WorkItem, WorkItemStatus, WorkItemType, WorkLog
)
from docuflow.features.work_items.system import WorkItemSystem, WorkItemFilters
from docuflow.infrastructure.config import Config

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="config")
def config_fixture():
    return Config(node_id="test_node")

@pytest.fixture(name="system")
def system_fixture(config: Config, session: Session):
    return WorkItemSystem(config=config, db_session=session)

@pytest.fixture(name="default_project")
def default_project_fixture(session: Session):
    project = Project(name="Default", is_default=True)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

class TestWorkItemSystemCreate:
    """Tests for the create_work_item() method."""

    def test_create_work_item(self, system: WorkItemSystem, default_project: Project):
        """Creating a new WorkItem."""
        wi = system.create_work_item(
            folder_name="SIDRA-353203-SHLAV-2",
            folder_path="path/to/folder",
            item_type=WorkItemType.SIDRA,
        )
        
        assert wi.id is not None
        assert wi.folder_name == "SIDRA-353203-SHLAV-2"
        assert wi.work_item_type == WorkItemType.SIDRA.value
        assert wi.status == WorkItemStatus.NEW.value
        assert wi.project_id == default_project.id

    def test_create_work_item_with_project_id(
        self, system: WorkItemSystem, session: Session
    ):
        """Creating a WorkItem with specific project_id."""
        project = Project(name="SHLAV-2")
        session.add(project)
        session.commit()
        
        wi = system.create_work_item(
            folder_name="SIDRA-111111-SHLAV-2",
            folder_path="path/to/folder",
            item_type=WorkItemType.SIDRA,
            project_id=project.id,
        )
        
        assert wi.project_id == project.id


class TestWorkItemSystemRetrieve:
    """Tests for the retrieve_work_item() method."""

    def test_retrieve_work_item(self, system: WorkItemSystem, default_project: Project):
        """Fetching a WorkItem by ID."""
        wi = system.create_work_item(
            folder_name="SIDRA-333333-SHLAV-2",
            folder_path="path/to/folder",
            item_type=WorkItemType.SIDRA,
        )
        
        retrieved = system.retrieve_work_item(wi.id)
        assert retrieved.id == wi.id

    def test_retrieve_nonexistent_raises(self, system: WorkItemSystem):
        """Fails for missing ID."""
        with pytest.raises(ValueError):
            system.retrieve_work_item(999999)


class TestWorkItemSystemList:
    """Tests for the list_work_items_by_filter() method."""

    def test_list_all_work_items(
        self, system: WorkItemSystem, default_project: Project
    ):
        system.create_work_item(folder_name="SIDRA-1", folder_path="p1", item_type=WorkItemType.SIDRA)
        system.create_work_item(folder_name="MIHTAV-1", folder_path="p2", item_type=WorkItemType.MIHTAV)
        
        items = system.list_work_items_by_filter(WorkItemFilters())
        assert len(items) == 2


class TestWorkItemSystemLifecycle:
    """Tests for status transitions and document registration."""

    def test_register_document(self, system: WorkItemSystem, default_project: Project):
        wi = system.create_work_item(folder_name="SIDRA-DOC", folder_path="p", item_type=WorkItemType.SIDRA)
        result = system.register_physical_document(wi.id, author="foreman1")
        
        assert result.status == WorkItemStatus.REGISTERED.value
        assert result.doc_received_at is not None

    def test_update_production_status(self, system: WorkItemSystem, default_project: Project):
        wi = system.create_work_item(folder_name="SIDRA-STATUS", folder_path="p", item_type=WorkItemType.SIDRA)
        
        # NEW -> REGISTERED
        system.update_production_status(wi.id, new_status=WorkItemStatus.REGISTERED)
        assert wi.status == WorkItemStatus.REGISTERED.value
        
        # REGISTERED -> IN_PROGRESS
        system.update_production_status(wi.id, new_status=WorkItemStatus.IN_PROGRESS)
        assert wi.status == WorkItemStatus.IN_PROGRESS.value

    def test_invalid_transition_raises(self, system: WorkItemSystem, default_project: Project):
        wi = system.create_work_item(folder_name="SIDRA-FAIL", folder_path="p", item_type=WorkItemType.SIDRA)
        # NEW -> DONE is illegal
        with pytest.raises(ValueError):
            system.update_production_status(wi.id, new_status=WorkItemStatus.DONE)
