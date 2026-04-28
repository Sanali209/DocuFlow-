"""Tests for remaining Task Board v2 compliance items."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    ProductionUnit,
    Project,
    TaskItem,
    TaskItemStatus,
    WorkItem,
)
from docuflow.features.analytics.system import AnalyticsSystem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.infrastructure.config import Config


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


@pytest.fixture(name="analytics")
def analytics_fixture(session):
    config = Config(node_id="test")
    return AnalyticsSystem(config, session)


@pytest.fixture(name="task_board")
def task_board_fixture(session, engine):
    config = Config(node_id="test")
    from unittest.mock import MagicMock

    ns = MagicMock()
    inv = MagicMock()
    prod = MagicMock()
    return TaskBoardSystem(
        config, engine, session, ns_mirror=ns, inventory_system=inv, production_system=prod
    )


class TestFindPalletsByProject:
    def test_find_pallets_by_project(self, session, task_board):
        """TaskBoardSystem should find pallets by project ID."""
        project = Project(name="Test")
        session.add(project)
        session.commit()

        wi = WorkItem(folder_name="WI-1", folder_path="/test", project_id=project.id)
        session.add(wi)
        session.flush()

        task = TaskItem(
            work_item_id=wi.id,
            file_name="test.gnc",
            file_path="test.gnc",
            status=TaskItemStatus.DONE,
        )
        session.add(task)
        session.flush()

        pallet = ProductionUnit(
            task_item_id=task.id,
            label_id="PALLET-001",
            qty_produced=10,
        )
        session.add(pallet)
        session.commit()

        pallets = task_board.find_pallets_by_project(project.id, session)
        assert len(pallets) == 1
        assert pallets[0].label_id == "PALLET-001"


class TestAnalyticsPalletByProject:
    def test_pallet_by_project_metric(self, session, analytics):
        """Analytics should include pallet_by_project metric."""
        project = Project(name="Test")
        session.add(project)
        session.commit()

        wi = WorkItem(folder_name="WI-1", folder_path="/test", project_id=project.id)
        session.add(wi)
        session.flush()

        task = TaskItem(
            work_item_id=wi.id,
            file_name="test.gnc",
            file_path="test.gnc",
            status=TaskItemStatus.DONE,
        )
        session.add(task)
        session.flush()

        pallet = ProductionUnit(
            task_item_id=task.id,
            label_id="PALLET-001",
            qty_produced=10,
        )
        session.add(pallet)
        session.commit()

        metrics = analytics.get_dashboard_metrics()
        assert "pallet_by_project" in metrics
        assert metrics["pallet_by_project"]["Test"] == 1
