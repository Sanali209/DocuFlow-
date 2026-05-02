from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.infrastructure import constants


@pytest.fixture
def orchestrator(tmp_path):
    from docuflow.infrastructure.config import Config
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    orch = P2POrchestrator(config)
    return orch


async def _run_one_cycle(orchestrator):
    """Run exactly one poll cycle of _polling_worker."""

    async def stop_after_sleep(*args, **kwargs):
        orchestrator._is_running = False

    with patch("docuflow.application.bus.orchestrator.anyio.sleep", side_effect=stop_after_sleep):
        orchestrator._is_running = True
        await orchestrator._polling_worker()


@pytest.mark.asyncio
async def test_failed_message_deleted_on_parse_error(orchestrator):
    """A message that fails parsing must be deleted from inbox to prevent infinite retry."""
    bad_msg = {"_filename": "REQ_SENDER_TEST_001.json", "invalid": True}
    orchestrator._bus = AsyncMock()
    orchestrator._bus.poll_messages = AsyncMock(return_value=[bad_msg])
    orchestrator._bus.delete_message = AsyncMock()
    orchestrator._dispatcher = MagicMock()

    await _run_one_cycle(orchestrator)

    orchestrator._bus.delete_message.assert_called_once_with(
        constants.BUS_INBOX_DIR, "REQ_SENDER_TEST_001.json"
    )


@pytest.mark.asyncio
async def test_successful_message_deleted_after_dispatch(orchestrator):
    """Successfully processed message is deleted from inbox."""
    import time

    from docuflow.domain.messages import CommandType, P2PMessage, P2PPayload
    from docuflow.infrastructure.security import HMACSigner

    signer = HMACSigner("test_secret")
    msg = P2PMessage(
        sender_id="NODE_B",
        sequence=1,
        timestamp=time.time(),
        payload=P2PPayload(command=CommandType.UPSERT_USER, data={}),
    )
    msg.signature = signer.sign(msg.to_signable_content())
    msg_data = msg.model_dump()
    msg_data["_filename"] = "BROADCAST_NODE_B_001.json"

    orchestrator._bus = AsyncMock()
    orchestrator._bus.poll_messages = AsyncMock(return_value=[msg_data])
    orchestrator._bus.delete_message = AsyncMock()

    from docuflow.application.bus.dispatcher import SecureDispatcher
    from docuflow.infrastructure.config import Config
    from docuflow.infrastructure.security import HMACSigner as HS

    config = Config(node_id="TEST")
    dispatcher = SecureDispatcher(config, HS("test_secret"))
    dispatcher.register_handler(CommandType.UPSERT_USER, lambda d: None)
    orchestrator._dispatcher = dispatcher

    await _run_one_cycle(orchestrator)

    orchestrator._bus.delete_message.assert_called_once_with(
        constants.BUS_INBOX_DIR, "BROADCAST_NODE_B_001.json"
    )
