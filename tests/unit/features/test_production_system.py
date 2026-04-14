from datetime import datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import (
    ProductionUnit,
    Project,
    TaskItem,
    WorkItem,
    WorkItemType,
)
from docuflow.features.production.system import ProductionSystem
from docuflow.features.projects.system import ProjectSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="config")
def config_fixture():
    """Создаёт тестовую конфигурацию."""
    return Config(node_id="NODE-01")


@pytest.fixture(name="session")
def session_fixture(engine):
    """Создаёт сессию для тестов."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="project_system")
def project_system_fixture(config: Config, session: Session):
    """Создаёт экземпляр ProjectSystem."""
    return ProjectSystem(config=config, db_session=session)


@pytest.fixture(name="production_system")
def production_system_fixture(config: Config, session: Session):
    """Создаёт экземпляр ProductionSystem."""
    return ProductionSystem(config=config, session=session)


def test_label_id_generation(production_system):
    label = production_system.create_unique_pallet_label(sequence_number=42)
    now = datetime.now()
    expected_prefix = f"{now.strftime('%y-%m')}-NODE-01"
    assert label.startswith(expected_prefix)
    assert label.endswith("0042")


def test_create_production_unit(production_system, session):
    """Test the registration of a finished production pallet."""
    project = Project(name="Project_FOR_UNIT", is_default=True)
    session.add(project)
    session.flush()
    project_id = project.id

    wi = WorkItem(
        folder_name="PROD-TEST-UNIQUE",
        folder_path="test/path",
        project_id=project_id,
        sidra_number="S-1",
        work_item_type=WorkItemType.SIDRA,
    )
    session.add(wi)
    session.flush()

    task = TaskItem(work_item_id=wi.id, file_name="part1.gnc", file_path="test/path/part1.gnc")
    session.add(task)
    session.flush()
    task_id = task.id

    # Create Unit
    unit = production_system.register_finished_pallet(
        task_item_id=task_id, quantity=50, author_name="operator_1"
    )

    assert unit.qty_produced == 50
    assert "NODE-01" in unit.label_id

    stored = session.get(ProductionUnit, unit.id)
    assert stored.task_item_id == task_id


def test_split_pallet(production_system, session):
    """Test splitting a production unit into two."""
    project = Project(name="Project_FOR_SPLIT", is_default=False)
    session.add(project)
    session.flush()
    project_id = project.id

    wi = WorkItem(
        folder_name="SPLIT-TEST-UNIQUE",
        folder_path="test/path",
        project_id=project_id,
        sidra_number="S-2",
        work_item_type=WorkItemType.SIDRA,
    )
    session.add(wi)
    session.flush()
    task = TaskItem(work_item_id=wi.id, file_name="part2.gnc", file_path="test/path/part2.gnc")
    session.add(task)
    session.flush()
    tid = task.id

    # Create original pallet
    original = production_system.register_finished_pallet(tid, quantity=100, author_name="boss")

    # Split 30 from 100
    new_unit = production_system.split_production_unit(
        original.id, move_quantity=30, author="worker"
    )

    # Verify
    assert original.qty_produced == 70
    assert new_unit.qty_produced == 30
    assert new_unit.parent_label_id == original.label_id
    assert new_unit.task_item_id == tid


def test_merge_pallets(production_system, session):
    """Test consolidating multiple pallets into a target unit."""
    project = Project(name="Project_FOR_MERGE", is_default=False)
    session.add(project)
    session.flush()
    project_id = project.id

    wi = WorkItem(
        folder_name="MERGE-TEST-UNIQUE",
        folder_path="test/path",
        project_id=project_id,
        sidra_number="S-3",
        work_item_type=WorkItemType.SIDRA,
    )
    session.add(wi)
    session.flush()
    task = TaskItem(work_item_id=wi.id, file_name="part3.gnc", file_path="test/path/part3.gnc")
    session.add(task)
    session.flush()
    tid = task.id

    # Create three pallets
    p1 = production_system.register_finished_pallet(tid, quantity=10, author_name="a")
    p2 = production_system.register_finished_pallet(tid, quantity=20, author_name="b")
    p3 = production_system.register_finished_pallet(tid, quantity=30, author_name="c")

    # Merge p1 and p2 into p3
    merged = production_system.merge_production_units(
        source_pallet_ids=[p1.id, p2.id], target_pallet_id=p3.id, author_name="supervisor"
    )

    # Verify
    assert merged.qty_produced == 60  # 10 + 20 + 30
    assert p1.qty_produced == 0
    assert p2.qty_produced == 0
    assert merged.id == p3.id
