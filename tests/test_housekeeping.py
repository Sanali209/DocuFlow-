import pytest
import anyio
import time
from pathlib import Path
from docuflow.infrastructure.housekeeping import HousekeepingSystem
from docuflow.infrastructure.config import Config

@pytest.fixture
def gc_setup(tmp_path):
    """Fixture for garbage collection testing."""
    shared_path = tmp_path / "shared"
    shared_path.mkdir()
    (shared_path / "BUS").mkdir()
    (shared_path / "BUS" / "INBOX").mkdir()
    (shared_path / "SNAPSHOTS").mkdir()
    
    config = Config(
        node_id="NODE_GC",
        shared_path=str(shared_path)
    )
    
    return config

@pytest.mark.anyio
async def test_gc_bus_cleanup(gc_setup):
    """Test that old bus files are cleaned up."""
    config = gc_setup
    gc = HousekeepingSystem(config=config)
    
    inbox = Path(config.shared_path) / "BUS" / "INBOX"
    
    # Create an old file (threshold is say 24h, but for test we'll use 0s for immediate)
    old_file = inbox / "REQ_OLD_001.json"
    old_file.write_text("{}")
    
    # Back-date the file
    # For the test we'll pass a custom age to the method.
    
    await gc.purge_stale_messages(max_age_seconds=-1) # -1 means everything is old
    
    assert not old_file.exists()

@pytest.mark.anyio
async def test_gc_snapshot_rotation(gc_setup):
    """Test that snapshot rotation keeps the last N snapshots."""
    config = gc_setup
    gc = HousekeepingSystem(config=config)
    
    snaps = Path(config.shared_path) / "SNAPSHOTS"
    
    # Create 5 snapshots
    for i in range(5):
        (snaps / f"SNAP_NODE_{i}.json").write_text("{}")
        # Ensure different mtimes
        time.sleep(0.01)
        
    # Rotate keeping only 2
    await gc.rotate_snapshots(keep_count=2)
    
    remaining = sorted(list(snaps.glob("SNAP_*.json")))
    assert len(remaining) == 2
    # Should be the most recent ones (3 and 4)
    assert "SNAP_NODE_4.json" in remaining[-1].name
