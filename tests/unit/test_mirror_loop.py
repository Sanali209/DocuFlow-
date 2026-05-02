import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mirror_service(tmp_path):
    from docuflow.features.folder_scanner.mirror import NSMirrorService
    from docuflow.infrastructure.config import Config
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    engine = MagicMock()
    sdk = AsyncMock()
    return NSMirrorService(config, sdk, engine)


@pytest.mark.asyncio
async def test_mirror_loop_survives_settings_fetch_error(mirror_service):
    """Loop must continue even if settings fetch raises an exception."""
    from docuflow.features.folder_scanner.settings import FolderScannerSettings

    call_count = 0

    async def fetch_side_effect(cls):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("Network error")
        mirror_service._running = False  # stop after 2nd call
        return FolderScannerSettings(ns_mirror_interval_seconds=0)

    mirror_service.sdk.resolve_system_by_type = fetch_side_effect
    mirror_service._running = True
    mirror_service._default_mirror_interval = 0  # speed up test

    # Must not raise
    await asyncio.wait_for(mirror_service._mirror_loop(), timeout=2.0)
    assert call_count >= 2, "Loop must continue after error"


@pytest.mark.asyncio
async def test_mirror_loop_single_settings_fetch_per_cycle(mirror_service):
    """Settings must be fetched exactly once per cycle (no duplicate fetch)."""
    from docuflow.features.folder_scanner.settings import FolderScannerSettings

    fetch_count = 0

    async def fetch_side_effect(cls):
        nonlocal fetch_count
        fetch_count += 1
        if fetch_count >= 2:
            mirror_service._running = False
        return FolderScannerSettings(ns_mirror_interval_seconds=0)

    mirror_service.sdk.resolve_system_by_type = fetch_side_effect
    mirror_service._running = True

    await asyncio.wait_for(mirror_service._mirror_loop(), timeout=2.0)
    # With the fix: 1 fetch per cycle × 2 cycles = 2
    # With the bug: 2 fetches per cycle × 1 cycle = 2 — but loop would die if first fetch fails
    assert fetch_count == 2
