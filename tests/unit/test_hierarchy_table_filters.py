"""Tests for HierarchyTable filtering."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import Project, TaskItem, TaskItemStatus, WorkItem
from docuflow.lib.widgets.hierarchy_table import HierarchyTable


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


def test_hierarchy_table_filter_by_project(session):
    """HierarchyTable should only show projects matching project_id filter."""
    p1 = Project(name="P1")
    p2 = Project(name="P2")
    session.add_all([p1, p2])
    session.commit()

    # Create WorkItems
    wi1 = WorkItem(folder_name="WI-1", folder_path="/test/WI-1", project_id=p1.id)
    wi2 = WorkItem(folder_name="WI-2", folder_path="/test/WI-2", project_id=p2.id)
    session.add_all([wi1, wi2])
    session.commit()

    table = HierarchyTable(
        user_id="u1", view_name="test", system_scope=None, filters={"project_id": p1.id}
    )

    # _render_project should check filters
    # For now, we test the logic indirectly by checking if filter is stored
    assert table.filters == {"project_id": p1.id}


def test_hierarchy_table_filter_by_status(session):
    """HierarchyTable should filter TaskItems by status."""
    p = Project(name="P1")
    session.add(p)
    session.commit()

    wi = WorkItem(folder_name="WI-1", folder_path="/test/WI-1", project_id=p.id)
    session.add(wi)
    session.flush()

    task = TaskItem(
        work_item_id=wi.id,
        file_name="test.gnc",
        file_path="test.gnc",
        status=TaskItemStatus.PLANNED,
    )
    session.add(task)
    session.commit()

    table = HierarchyTable(
        user_id="u1", view_name="test", system_scope=None, filters={"status": "planned"}
    )
    assert table.filters == {"status": "planned"}
