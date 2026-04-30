from unittest.mock import AsyncMock, MagicMock

import pytest

from docuflow.infrastructure.sync import DataSyncSystem


@pytest.fixture
def sync_system(tmp_path):
    from docuflow.infrastructure.config import Config
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    engine = MagicMock()
    return DataSyncSystem(config, engine)


@pytest.mark.asyncio
async def test_broadcast_entity_update_calls_broadcast_command(sync_system):
    """broadcast_entity_update must call broadcast_command, not broadcast_request."""
    orchestrator = AsyncMock()
    orchestrator.broadcast_command = AsyncMock()
    # Ensure broadcast_request does NOT exist
    if hasattr(orchestrator, 'broadcast_request'):
        del orchestrator.broadcast_request
    sync_system.set_orchestrator(orchestrator)

    import datetime

    from pydantic import BaseModel

    class FakeEntity(BaseModel):
        id: int | None = None
        updated_at: datetime.datetime | None = None

        def model_dump(self):
            return {"id": self.id, "updated_at": self.updated_at}

    entity = FakeEntity()
    await sync_system.broadcast_entity_update(entity)
    orchestrator.broadcast_command.assert_called_once()
