from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_send_message_calls_write_message(tmp_path):
    """send_message must call write_message on FileBusSystem, not broadcast_message."""
    from sqlmodel import Session, SQLModel, create_engine

    from docuflow.features.chat.system import ChatSystem
    from docuflow.infrastructure.config import Config

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    session = Session(engine)

    mock_bus = AsyncMock()
    mock_bus.write_message = AsyncMock(return_value="msg_id")

    sdk = AsyncMock()
    sdk.resolve_system_by_type = AsyncMock(return_value=mock_bus)

    system = ChatSystem(config, session, sdk=sdk)
    await system.send_message(author="test", content="hello")

    mock_bus.write_message.assert_called_once()
    session.close()
