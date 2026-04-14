import pytest
from sqlalchemy import Engine
from sqlmodel import SQLModel

from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.features.folder_scanner.system import FolderScannerSystem
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.di import AppProvider
from docuflow.sdk import SDK


@pytest.fixture
def mock_config():
    c = Config()
    c.node_id = "test_infra_node"
    # Use in-memory for engine
    c.database_url = "sqlite:///:memory:"
    c.shared_path = "./tmp_test_shared"
    return c


@pytest.mark.asyncio
async def test_sdk_full_initialization_smoke(mock_config):
    """Verify SDK correctly initializes all systems and handlers."""
    provider = AppProvider(mock_config)
    from dishka import make_async_container

    container = make_async_container(provider)

    engine = await container.get(Engine)
    SQLModel.metadata.create_all(engine)

    sdk = SDK(container)

    try:
        # Full startup triggers all registrations
        await sdk.on_startup()
        print("✅ SDK Startup successful")

        async with container() as req:
            # 1. Check Orchestrator handlers
            orchestrator = await req.get(P2POrchestrator)
            from docuflow.domain.messages import CommandType

            # Should now have handlers registered via AdminSyncSystem startup
            assert CommandType.UPSERT_ROLE in orchestrator._dispatcher._handlers
            print("✅ P2P Handlers verified")

            # 2. Check Scanner
            scanner = await req.get(FolderScannerSystem)
            assert scanner.get_ingestion_status()["is_active"] is True
            print("✅ Scanner is active")

    finally:
        await sdk.on_shutdown()
        await container.close()
        print("✅ Cleanup complete")


@pytest.mark.asyncio
async def test_scanner_standalone_smoke(mock_config):
    """Smoke check for scanner without full SDK startup."""
    provider = AppProvider(mock_config)
    from dishka import make_async_container

    container = make_async_container(provider)

    async with container() as req:
        scanner = await req.get(FolderScannerSystem)
        status = scanner.get_ingestion_status()
        assert "items_found" in status
        print("✅ Scanner status ok")
    await container.close()
