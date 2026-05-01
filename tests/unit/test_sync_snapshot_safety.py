import pytest
from unittest.mock import MagicMock


def make_sync(tmp_path):
    from docuflow.infrastructure.config import Config
    from docuflow.infrastructure.sync import DataSyncSystem

    config = Config(node_id="TEST", shared_path=str(tmp_path))
    return DataSyncSystem(config, MagicMock())


@pytest.mark.asyncio
async def test_apply_remote_snapshot_handles_corrupted_json(tmp_path):
    """Corrupted snapshot must not raise — must log and return gracefully."""
    sync = make_sync(tmp_path)
    bad_snap = tmp_path / "corrupt.json"
    bad_snap.write_text("{ this is not valid JSON !!!")

    # Must not raise
    await sync.apply_remote_snapshot(bad_snap)


@pytest.mark.asyncio
async def test_apply_remote_snapshot_handles_empty_file(tmp_path):
    """Empty snapshot file must not raise — must log and return gracefully."""
    sync = make_sync(tmp_path)
    empty_snap = tmp_path / "empty.json"
    empty_snap.write_bytes(b"")

    # Must not raise
    await sync.apply_remote_snapshot(empty_snap)
