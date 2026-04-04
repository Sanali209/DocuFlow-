import pytest
import anyio
import time
import json
from pathlib import Path
from docuflow.infrastructure.coordination import CoordinationSystem
from docuflow.infrastructure.config import Config

@pytest.fixture
def sync_config(tmp_path):
    """Fixture for coordination testing with short timeouts."""
    shared_path = tmp_path / "shared"
    shared_path.mkdir()
    
    return Config(
        node_id="NODE_A",
        shared_path=str(shared_path),
        heartbeat_interval=1,
        coordinator_timeout=2
    )

@pytest.mark.anyio
async def test_leader_election_initial(sync_config):
    """Test that a node can become leader if no lock exists."""
    coord = CoordinationSystem(config=sync_config)
    
    is_leader = await coord.try_become_leader()
    assert is_leader is True
    assert coord.is_leader is True
    
    lock_file = Path(sync_config.shared_path) / ".coordinator.lock"
    assert lock_file.exists()
    
    with open(lock_file, "r") as f:
        data = json.load(f)
        assert data["node_id"] == "NODE_A"

@pytest.mark.anyio
async def test_leader_election_contention(sync_config):
    """Test that Node B cannot become leader if Node A holds a fresh lock."""
    # Node A becomes leader
    coord_a = CoordinationSystem(config=sync_config)
    await coord_a.try_become_leader()
    
    # Node B tries to become leader
    config_b = Config(
        node_id="NODE_B", 
        shared_path=sync_config.shared_path,
        heartbeat_interval=1,
        coordinator_timeout=2
    )
    coord_b = CoordinationSystem(config=config_b)
    is_leader_b = await coord_b.try_become_leader()
    
    assert is_leader_b is False
    assert coord_b.is_leader is False

@pytest.mark.anyio
async def test_leader_election_failover(sync_config):
    """Test that Node B becomes leader after Node A's lock expires."""
    coord_a = CoordinationSystem(config=sync_config)
    await coord_a.try_become_leader()
    
    # Wait for timeout (timeout=2)
    await anyio.sleep(2.5)
    
    config_b = Config(
        node_id="NODE_B", 
        shared_path=sync_config.shared_path,
        heartbeat_interval=1,
        coordinator_timeout=2
    )
    coord_b = CoordinationSystem(config=config_b)
    is_leader_b = await coord_b.try_become_leader()
    
    assert is_leader_b is True
    assert coord_b.is_leader is True
