"""Tests for pallet display in hierarchy rows."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    ProductionUnit,
    Project,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
    WorkItem,
)
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.lib.widgets.hierarchy_table import HierarchyTable


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


def _make_done_task_with_pallet(session: Session, tg: TaskGroup, wi: WorkItem):
    """Helper: create a DONE task with an associated pallet."""
    task = TaskItem(
        file_name="T.GNC",
        file_path="/test/T.GNC",
        work_item_id=wi.id,
        task_group_id=tg.id,
        status=TaskItemStatus.DONE,
        sheets_done=8,
        sheet_qty=8,
        qty_produced=47,
    )
    session.add(task)
    session.flush()

    pallet = ProductionUnit(
        label_id="26-04-LASER_1-0015",
        qty_produced=47,
        task_item_id=task.id,
        is_stock=True,
    )
    session.add(pallet)
    session.commit()
    return task, pallet


def test_taskgroup_line2_shows_pallet_details(session: Session):
    """
    TaskGroup row for a group with DONE tasks must show individual
    pallet labels with quantities, not just a count.
    """
    # Arrange
    project = Project(name="P1")
    session.add(project)
    session.flush()

    wi = WorkItem(folder_name="WI1", folder_path="/test/WI1", project_id=project.id)
    session.add(wi)
    session.flush()

    tg = TaskGroup(name="Steel 4mm", work_item_id=wi.id)
    session.add(tg)
    session.flush()

    _make_done_task_with_pallet(session, tg, wi)

    # We need to test the line2 that HierarchyTable builds.
    # _render_taskgroup builds line2 internally; to avoid full UI rendering
    # we extract the helper that builds the descriptive string.
    table = HierarchyTable(user_id="u1", view_name="test", system_scope=None)
    tb_system = TaskBoardSystem(config=None, db_engine=session.get_bind())

    # Act: call the internal line2 builder (we will extract it in the fix)
    line2 = table._build_taskgroup_line2(session, tb_system, tg)

    # Assert: must contain pallet label and quantity
    assert "26-04-LASER_1-0015" in line2
    assert "47" in line2
    assert "📦" in line2
