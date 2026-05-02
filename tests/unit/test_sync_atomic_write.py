import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_write_snapshot_atomically_uses_temp_then_rename(tmp_path):
    """Snapshot write must use temp file then os.replace for atomicity."""
    from docuflow.infrastructure.config import Config
    from docuflow.infrastructure.sync import DataSyncSystem

    config = Config(node_id="TEST", shared_path=str(tmp_path))
    system = DataSyncSystem(config, MagicMock())

    target = tmp_path / "test_snapshot.json"
    data = {"users": [{"id": 1, "name": "Test"}]}

    await system._write_snapshot_atomically(target, data)

    # File must exist with correct content
    assert target.exists()
    assert json.loads(target.read_text()) == data

    # Temp file must be cleaned up
    temp = tmp_path / f"TEMP_{target.name}"
    assert not temp.exists(), "Temp file must be removed after rename"


@pytest.mark.asyncio
async def test_write_snapshot_atomically_no_corrupt_on_failure(tmp_path):
    """Existing snapshot must be untouched if write fails."""
    from docuflow.infrastructure.config import Config
    from docuflow.infrastructure.sync import DataSyncSystem

    config = Config(node_id="TEST", shared_path=str(tmp_path))
    system = DataSyncSystem(config, MagicMock())

    # Pre-existing snapshot
    target = tmp_path / "existing.json"
    original_data = {"users": [{"id": 1}]}
    target.write_text(json.dumps(original_data))

    # Simulate write failure
    with patch("anyio.Path.write_text", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            await system._write_snapshot_atomically(target, {"new": "data"})

    # Original file must be untouched
    assert json.loads(target.read_text()) == original_data

    # Temp file must be cleaned up on failure
    temp = tmp_path / f"TEMP_{target.name}"
    assert not temp.exists(), "Temp file must be removed even when write fails"
