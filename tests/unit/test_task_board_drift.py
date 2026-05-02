import pytest
from sqlmodel import Session, SQLModel, create_engine

# Import models before fixtures so SQLModel.metadata is populated for create_all
import docuflow.domain.entities.production  # noqa: F401


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def task_board(engine, tmp_path):
    from docuflow.features.task_board.system import TaskBoardSystem
    from docuflow.infrastructure.config import Config
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    return TaskBoardSystem(config, engine)


def test_get_node_drift_empty_bucket(task_board):
    """get_node_drift returns 0.0 for empty bucket (no nested session errors)."""
    result = task_board.get_node_drift("NODE_1")
    assert result == 0.0


def test_get_node_drift_with_completed_tasks(engine, tmp_path):
    """get_node_drift correctly calculates drift without nested session errors."""

    from docuflow.domain.entities.production import (
        Project,
        TaskItem,
        TaskItemStatus,
        WorkerBucketEntry,
        WorkItem,
    )
    from docuflow.features.task_board.system import TaskBoardSystem
    from docuflow.infrastructure.config import Config

    # Seed data
    with Session(engine) as session:
        project = Project(name="Test")
        session.add(project)
        session.flush()
        wi = WorkItem(folder_name="test", folder_path=".", project_id=project.id)
        session.add(wi)
        session.flush()
        task = TaskItem(
            work_item_id=wi.id,
            file_name="t.gnc",
            file_path="t.gnc",
            status=TaskItemStatus.DONE,
            estimated_minutes=60,
            actual_minutes=90,
            assigned_to_node="NODE_1",
        )
        session.add(task)
        session.flush()
        bucket = WorkerBucketEntry(node_id="NODE_1", task_item_id=task.id)
        session.add(bucket)
        session.commit()

    config = Config(node_id="TEST", shared_path=str(tmp_path))
    board = TaskBoardSystem(config, engine)
    drift = board.get_node_drift("NODE_1")
    assert drift == pytest.approx(50.0)  # (90-60)/60 * 100 = 50%
