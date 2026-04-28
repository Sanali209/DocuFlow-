import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    Project,
    WorkItem,
    WorkItemStatus,
    WorkItemType,
    WorkLog,
)
from docuflow.features.projects.system import ProjectSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="config")
def config_fixture():
    """Создаёт тестовую конфигурацию."""
    return Config(node_id="test_node")


@pytest.fixture(name="session")
def session_fixture(engine):
    """Создаёт сессию для тестов."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="project_system")
def project_system_fixture(config: Config, session: Session):
    """Создаёт экземпляр ProjectSystem."""
    return ProjectSystem(config=config, db_session=session)


def test_ensure_default_project(project_system, session):
    """Test resolution of the default workshop project."""
    # Before
    assert session.get(Project, 1) is None

    project_system.resolve_default_workshop_project()

    # After
    p = session.get(Project, 1)
    assert p is not None
    assert p.name == "Default"


def test_create_and_list_projects(project_system, engine):
    project_system.resolve_default_workshop_project()
    project_system.register_new_project("Project A", "Description A")
    project_system.register_new_project("Project B")

    projects = project_system.get_all_active_projects()
    names = [p.name for p in projects]
    assert "Default" in names
    assert "Project A" in names
    assert "Project B" in names


def test_reassign_work_item(project_system, session):
    """Test reassigning a production group to a different project."""
    # Setup
    wi = WorkItem(
        folder_name="TEST-WI",
        folder_path="test/path",
        work_item_type=WorkItemType.SIDRA,
        project_id=1,  # Default
        status=WorkItemStatus.NEW,
    )
    session.add(wi)
    session.flush()
    session.refresh(wi)
    wi_id = wi.id

    p2 = project_system.register_new_project("New Project")

    # Reassign
    updated_wi = project_system.reassign_production_group(wi_id, p2.id)

    assert updated_wi.project_id == p2.id

    # Check Logs
    logs = session.exec(select(WorkLog).where(WorkLog.work_item_id == wi_id)).all()
    assert any("New Project" in l.message for l in logs)
