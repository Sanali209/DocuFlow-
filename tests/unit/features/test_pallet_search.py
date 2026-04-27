"""Tests for pallet search methods in TaskBoardSystem."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import ProductionUnit, Project, TaskItem, WorkItem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.infrastructure.config import Config


@pytest.fixture(name="engine")
def engine_fixture():
    """Creates an in-memory SQLite engine for tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """Creates an in-memory SQLite session for tests."""
    with Session(engine) as session:
        yield session


class TestPalletSearch:
    """Tests for pallet search methods."""

    def test_find_pallets_by_task(self, session: Session):
        """Find pallets by task item ID."""
        task = TaskItem(work_item_id=1, file_name="test.gnc", file_path="test.gnc")
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.id is not None

        pallet = ProductionUnit(label_id="TEST-001", task_item_id=task.id, qty_produced=10)
        session.add(pallet)
        session.commit()

        tbs = TaskBoardSystem(config=Config(node_id="test"), db_engine=None, session=session)
        pallets = tbs.find_pallets_by_task(task.id, session)
        assert len(pallets) == 1
        assert pallets[0].label_id == "TEST-001"

    def test_find_pallets_by_work_item(self, session: Session):
        """Find pallets by work item ID."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        assert project.id is not None

        work_item = WorkItem(folder_name="test", folder_path="/test", project_id=project.id)
        session.add(work_item)
        session.commit()
        session.refresh(work_item)

        assert work_item.id is not None

        task = TaskItem(work_item_id=work_item.id, file_name="test.gnc", file_path="test.gnc")
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.id is not None

        pallet = ProductionUnit(label_id="TEST-002", task_item_id=task.id, qty_produced=5)
        session.add(pallet)
        session.commit()

        tbs = TaskBoardSystem(config=Config(node_id="test"), db_engine=None, session=session)
        pallets = tbs.find_pallets_by_work_item(work_item.id, session)
        assert len(pallets) == 1
        assert pallets[0].label_id == "TEST-002"

    def test_find_task_by_pallet_label(self, session: Session):
        """Find task by pallet label ID."""
        task = TaskItem(work_item_id=1, file_name="test.gnc", file_path="test.gnc")
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.id is not None

        pallet = ProductionUnit(label_id="TEST-003", task_item_id=task.id, qty_produced=20)
        session.add(pallet)
        session.commit()

        tbs = TaskBoardSystem(config=Config(node_id="test"), db_engine=None, session=session)
        found_task = tbs.find_task_by_pallet_label("TEST-003", session)
        assert found_task is not None
        assert found_task.id == task.id

    def test_find_task_by_pallet_label_not_found(self, session: Session):
        """Return None when pallet label is not found."""
        tbs = TaskBoardSystem(config=Config(node_id="test"), db_engine=None, session=session)
        found_task = tbs.find_task_by_pallet_label("NONEXISTENT", session)
        assert found_task is None
