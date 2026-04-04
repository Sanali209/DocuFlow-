import pytest
from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.infrastructure.config import Config
from tests.helpers import create_test_sdk

@pytest.mark.anyio
async def test_orchestrator_lifecycle_with_di():
    """TDD: Verify that P2POrchestrator can start and stop through the SDK.
    
    This integration test ensures that the orchestrator is correctly resolved
    with its myriad infrastructure dependencies and responds to lifecycle hooks.
    """
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
