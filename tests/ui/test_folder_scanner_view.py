from unittest.mock import AsyncMock, MagicMock

import pytest

nicegui = pytest.importorskip("nicegui")
if not hasattr(nicegui, "testing") or not hasattr(nicegui.testing, "user_simulation"):
    pytest.skip("requires nicegui.testing.user_simulation", allow_module_level=True)
from nicegui.testing import user_simulation
from sqlalchemy import Engine

from docuflow.features.folder_scanner.settings import FolderScannerSettings
from docuflow.features.folder_scanner.view import folder_scanner_view


@pytest.mark.asyncio
async def test_folder_scanner_view_master_status():
    """Verify that the Folder Scanner view displays MASTER status when SDK reports as master."""
    # 1. Setup mocks
    sdk = AsyncMock()
    sdk.is_master.return_value = True
    # resolve_system_by_type should return a system or settings object
    scanner = AsyncMock()
    settings = FolderScannerSettings(sidra_scan_path="Z:/TEST", poll_interval_seconds=60)

    async def mock_resolve(cls):
        if cls == FolderScannerSettings:
            return settings
        return scanner

    sdk.resolve_system_by_type.side_effect = mock_resolve

    config = MagicMock()
    config.node_id = "node_01"
    engine = MagicMock(spec=Engine)

    # 2. Render and simulate
    async with user_simulation(lambda: folder_scanner_view(sdk, config, engine)) as user:
        await user.open("/")

        # Check for Master status indicator
        await user.should_see("MASTER NODE: node_01")
        await user.should_see("Folder Ingestion & NC Mirror")

        # Check if settings are displayed
        await user.should_see("SIDRA PATH")
        await user.should_see("Z:/TEST")


@pytest.mark.asyncio
async def test_folder_scanner_scan_trigger():
    """Verify the 'SCAN NOW' button triggers the scanner."""
    sdk = AsyncMock()
    sdk.is_master.return_value = True
    scanner = AsyncMock()

    async def mock_resolve(cls):
        if cls == FolderScannerSettings:
            return FolderScannerSettings()
        return scanner

    sdk.resolve_system_by_type.side_effect = mock_resolve

    config = MagicMock()
    engine = MagicMock()

    async with user_simulation(lambda: folder_scanner_view(sdk, config, engine)) as user:
        await user.open("/")

        # Click SCAN NOW
        user.find("SCAN NOW").click()

        # Check if scanner.scan_now was called
        scanner.scan_now.assert_called_once()
        await user.should_see("Manual Scan Triggered...")
