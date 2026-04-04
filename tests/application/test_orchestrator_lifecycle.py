import pytest
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock
from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.domain.messages import CommandType
from docuflow.infrastructure.config import Config

@pytest.mark.anyio
async def test_orchestrator_lifecycle_with_di():
    """TDD: Verify that P2POrchestrator can start and stop through the SDK.
    
    This integration test ensures that the orchestrator is correctly resolved
    with its myriad infrastructure dependencies and responds to lifecycle hooks.
    """
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    from tests.helpers import create_test_sdk

    config = Config(node_id="TEST_ORCH")
    sdk = await create_test_sdk(config)
    
    # Resolve orchestrator from the real container
    orchestrator = await sdk.resolve_system_by_type(P2POrchestrator)
    
    # SDK.on_startup() was already called by create_test_sdk()
    # P2POrchestrator.on_startup() should have been triggered (will implement Task 3.1 later)
    # For now, we call it manually to verify the system logic.
    
    await orchestrator.on_startup()
    assert orchestrator.is_running is True
    
    await orchestrator.on_shutdown()
    assert orchestrator.is_running is False
    
    await sdk.on_shutdown()

@pytest.mark.anyio
async def test_orchestrator_broadcast_command_writes_signed_message():
    """Critical path: broadcast_command must emit a signed P2P envelope into the bus."""
    config = Config(node_id="TEST_ORCH_BROADCAST")

    coordination = MagicMock()
    coordination.is_leader = True

    bus = MagicMock()
    bus.write_message = AsyncMock()

    sync = MagicMock()
    housekeeping = MagicMock()
    dispatcher = MagicMock()
    signer = MagicMock()
    signer.sign.return_value = "signed-payload"
    admin_sync = MagicMock()

    orchestrator = P2POrchestrator(
        config,
        coordination,
        bus,
        sync,
        housekeeping,
        dispatcher,
        signer,
        admin_sync,
    )

    await orchestrator.broadcast_command(CommandType.FORCE_STEP_DOWN, {"cooldown": 5})

    bus.write_message.assert_awaited_once()
    payload = bus.write_message.await_args.args[0]

    assert payload["sender_id"] == "TEST_ORCH_BROADCAST"
    assert payload["sequence"] == 1
    assert payload["payload"]["command"] == CommandType.FORCE_STEP_DOWN.value
    assert payload["payload"]["data"] == {"cooldown": 5}
    assert payload["signature"] == "signed-payload"
    signer.sign.assert_called_once()
