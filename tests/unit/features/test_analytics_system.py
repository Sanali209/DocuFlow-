import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    Project,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
    WorkItem,
)
from docuflow.features.analytics.system import AnalyticsSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def analytics_system(session: Session):
    config = Config(node_id="test_node")
    return AnalyticsSystem(config, session)


@pytest.fixture
def seeded_session(session: Session):
    project = Project(name="Test Project")
    session.add(project)
    session.commit()
    session.refresh(project)

    wi = WorkItem(project_id=project.id, folder_name="WI-001", folder_path="./WI-001")
    session.add(wi)
    session.commit()
    session.refresh(wi)

    tg = TaskGroup(name="TG-1", work_item_id=wi.id)
    session.add(tg)
    session.commit()
    session.refresh(tg)

    t1 = TaskItem(
        work_item_id=wi.id,
        task_group_id=tg.id,
        file_name="task1.gnc",
        file_path="./task1.gnc",
        status=TaskItemStatus.DONE,
        assigned_to_node="node-a",
        estimated_minutes=60,
        actual_minutes=65,
    )
    t2 = TaskItem(
        work_item_id=wi.id,
        task_group_id=tg.id,
        file_name="task2.gnc",
        file_path="./task2.gnc",
        status=TaskItemStatus.IN_PROGRESS,
        assigned_to_node="node-a",
    )
    t3 = TaskItem(
        work_item_id=wi.id,
        file_name="task3.gnc",
        file_path="./task3.gnc",
        status=TaskItemStatus.PLANNED,
        assigned_to_node="node-b",
    )
    session.add_all([t1, t2, t3])
    session.commit()
    return session


def test_dashboard_metrics_new_fields(analytics_system: AnalyticsSystem, seeded_session: Session):
    analytics_system.session = seeded_session
    metrics = analytics_system.get_dashboard_metrics()

    assert metrics["total_task_groups"] == 1
    assert "groups_by_status" in metrics
    assert "node_utilization" in metrics

    # One group with IN_PROGRESS among other statuses -> in_progress
    assert metrics["groups_by_status"].get("in_progress", 0) == 1

    # Node utilization
    assert "node-a" in metrics["node_utilization"]
    assert metrics["node_utilization"]["node-a"]["active"] == 1
    assert metrics["node_utilization"]["node-a"]["done"] == 1
    assert metrics["node_utilization"]["node-a"]["queued"] == 0

    assert "node-b" in metrics["node_utilization"]
    assert metrics["node_utilization"]["node-b"]["queued"] == 1
