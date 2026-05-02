import asyncio
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def production_system(tmp_path):
    from sqlmodel import Session, SQLModel, create_engine

    from docuflow.features.production.system import ProductionSystem
    from docuflow.infrastructure.config import Config
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    session = Session(engine)
    return ProductionSystem(config, session)


@pytest.mark.asyncio
async def test_broadcast_command_is_scheduled_not_dropped(production_system, tmp_path):
    """broadcast_command must be scheduled as a task, not silently dropped."""
    from sqlmodel import Session, SQLModel, create_engine

    from docuflow.domain.entities.production import Project, TaskItem, WorkItem

    # Set up DB with required entities
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        project = Project(name="Test")
        session.add(project)
        session.flush()
        wi = WorkItem(folder_name="test", folder_path=".", project_id=project.id)
        session.add(wi)
        session.flush()
        task = TaskItem(work_item_id=wi.id, file_name="t.gnc", file_path="t.gnc")
        session.add(task)
        session.commit()
        session.refresh(task)
        task_id = task.id

    broadcast_called = False

    async def fake_broadcast(command, data):
        nonlocal broadcast_called
        broadcast_called = True

    mock_orchestrator = MagicMock()
    mock_orchestrator.broadcast_command = fake_broadcast

    mock_sdk = MagicMock()
    mock_sdk.orchestrator = mock_orchestrator

    production_system.sdk = mock_sdk
    production_system._db_session = Session(engine)

    production_system.register_finished_pallet(task_item_id=task_id, quantity=5, author_name="test")

    # Allow any scheduled tasks to run
    await asyncio.sleep(0)

    assert broadcast_called, "broadcast_command coroutine was not awaited/scheduled"
