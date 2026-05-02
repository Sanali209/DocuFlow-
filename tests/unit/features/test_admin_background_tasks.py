import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.features.admin.system import AdminSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def admin_system():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    orchestrator = MagicMock()
    orchestrator.broadcast_command = AsyncMock()
    signer = MagicMock()
    config = Config()
    return AdminSystem(session=session, orchestrator=orchestrator, signer=signer, config=config)


@pytest.mark.asyncio
async def test_background_tasks_are_tracked(admin_system):
    """Background tasks created via create_task should be stored to prevent GC."""
    system = admin_system

    # Call a method that creates a background task
    system.force_global_step_down()

    # VERIFY: task is tracked (not fire-and-forget)
    assert len(system._background_tasks) > 0
    task = system._background_tasks[0]
    assert not task.done() or task.exception() is None


@pytest.mark.asyncio
async def test_background_task_exception_does_not_crash(admin_system):
    """Exceptions in background tasks should be logged, not crash the event loop."""
    system = admin_system
    system._orchestrator.broadcast_command = AsyncMock(side_effect=RuntimeError("P2P fail"))

    # This should NOT raise — exception is caught inside create_task wrapper
    system.force_global_step_down()

    # Let the task run
    tasks = [t for t in system._background_tasks if not t.done()]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    # Verify the task completed (exception was swallowed)
    for t in system._background_tasks:
        assert t.done()
        assert t.exception() is None
