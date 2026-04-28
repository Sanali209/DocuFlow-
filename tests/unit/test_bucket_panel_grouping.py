"""Tests for BucketPanel grouping logic."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    Project,
    TaskGroup,
    TaskItem,
    WorkerBucketEntry,
    WorkItem,
)
from docuflow.lib.widgets.bucket_panel import BucketPanel


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_group_by_task_group_instead_of_batch_group_id(session: Session):
    """
    WorkerBucketEntry entries with different legacy batch_group_id values
    but whose tasks belong to the same TaskGroup must be grouped together.
    """
    # Arrange: create project + work item
    project = Project(name="P1")
    session.add(project)
    session.flush()

    wi = WorkItem(folder_name="WI1", folder_path="/test/WI1", project_id=project.id)
    session.add(wi)
    session.flush()

    # Create two TaskGroups
    tg1 = TaskGroup(name="Steel 4mm", work_item_id=wi.id)
    tg2 = TaskGroup(name="Steel 5mm", work_item_id=wi.id)
    session.add(tg1)
    session.add(tg2)
    session.flush()

    # Create tasks belonging to tg1 and tg2
    t1 = TaskItem(
        file_name="A.GNC", file_path="/test/A.GNC",
        work_item_id=wi.id, task_group_id=tg1.id,
    )
    t2 = TaskItem(
        file_name="B.GNC", file_path="/test/B.GNC",
        work_item_id=wi.id, task_group_id=tg1.id,
    )
    t3 = TaskItem(
        file_name="C.GNC", file_path="/test/C.GNC",
        work_item_id=wi.id, task_group_id=tg2.id,
    )
    session.add(t1)
    session.add(t2)
    session.add(t3)
    session.flush()

    # Create bucket entries with DIFFERENT legacy batch_group_id strings
    e1 = WorkerBucketEntry(
        node_id="LASER_1",
        task_item_id=t1.id,
        batch_group_id="legacy-batch-999",
    )
    e2 = WorkerBucketEntry(
        node_id="LASER_1",
        task_item_id=t2.id,
        batch_group_id="legacy-batch-888",
    )
    e3 = WorkerBucketEntry(
        node_id="LASER_1",
        task_item_id=t3.id,
        batch_group_id="legacy-batch-777",
    )
    session.add(e1)
    session.add(e2)
    session.add(e3)
    session.commit()

    # Act: use BucketPanel grouping logic
    panel = BucketPanel(node_id="LASER_1", user="admin", system_scope=None)
    result = panel._group_by_batch(session, [e1, e2, e3])

    # Assert: grouped by task_group_id, NOT by batch_group_id
    # tg1 has 2 tasks, tg2 has 1 task
    assert len(result) == 2, f"Expected 2 groups (one per TaskGroup), got {len(result)}"

    # Find the group with 2 tasks — it must be tg1
    group_sizes = [len(tasks) for tasks in result.values()]
    assert sorted(group_sizes) == [1, 2]

    # Ensure legacy batch IDs are NOT keys
    assert "legacy-batch-999" not in result
    assert "legacy-batch-888" not in result
    assert "legacy-batch-777" not in result
