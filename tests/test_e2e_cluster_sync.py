import pytest
import anyio
import os
import json
from pathlib import Path
from docuflow.infrastructure.config import Config
from docuflow.application.bus.orchestrator import P2POrchestrator
from tests.helpers import create_test_sdk

@pytest.mark.anyio
async def test_e2e_cluster_failover_and_sync(tmp_path):
    """TDD: Full E2E cluster verification of leader election and failover.
    
    This test serves as the ultimate proof of Task 4.1 and the DocuFlow
    P2P architecture, demonstrating automated coordination and 
    synchronization across independent SDK nodes sharing a common filesystem.
    """
    shared_root = tmp_path / "shared"
    shared_root.mkdir()
    
    # Configuration with aggressive intervals for fast test execution
    common_params = {
        "shared_path": str(shared_root),
        "heartbeat_interval": 0.2,    # 200ms heartbeats
        "coordinator_timeout": 0.5,   # 500ms timeout for failover
        "sync_check_interval": 0.3    # 300ms sync check
    }
    
    config_a = Config(
        node_id="NODE_A",
        database_url=f"sqlite:///{tmp_path}/node_a.db",
        **common_params
    )
    
    config_b = Config(
        node_id="NODE_B",
        database_url=f"sqlite:///{tmp_path}/node_b.db",
        **common_params
    )
    
    # Ensure bus directories exist for both
    for node_path in [config_a.shared_path, config_b.shared_path]:
        p = Path(node_path)
        (p / "BUS" / "INBOX").mkdir(parents=True, exist_ok=True)
        (p / "BUS" / "OUTBOX").mkdir(parents=True, exist_ok=True)

    # 1. Start Node A
    sdk_a = await create_test_sdk(config_a)
    orch_a = await sdk_a.resolve_system_by_type(P2POrchestrator)
    
    # 2. Start Node B
    sdk_b = await create_test_sdk(config_b)
    orch_b = await sdk_b.resolve_system_by_type(P2POrchestrator)
    
    # Give them time to elect a leader and run one maintenance cycle
    await anyio.sleep(1.0)
    
    # 3. Verify Coordination: Only one should be leader
    from docuflow.infrastructure.coordination import CoordinationSystem
    coord_a = await sdk_a.resolve_system_by_type(CoordinationSystem)
    coord_b = await sdk_b.resolve_system_by_type(CoordinationSystem)
    
    leaders = [c.node_id for c in [coord_a, coord_b] if c.is_leader]
    assert len(leaders) == 1, f"Expected 1 leader, found: {leaders}"
    
    active_leader_id = leaders[0]
    follower_sdk = sdk_b if active_leader_id == "NODE_A" else sdk_a
    leader_sdk = sdk_a if active_leader_id == "NODE_A" else sdk_b
    
    # 4. Verify Snapshot: The leader should have created a snapshot
    snapshot_dir = shared_root / "SNAPSHOTS"
    assert snapshot_dir.exists()
    snapshots = list(snapshot_dir.glob("SNAP_*.json"))
    assert len(snapshots) >= 1, "Leader failed to create initial snapshot"
    
    # 5. Failover: Kill the leader
    await leader_sdk.on_shutdown()
    print(f"Killed Leader: {active_leader_id}")
    
    # Wait for the timeout (0.5s) plus some buffer
    await anyio.sleep(1.0)
    
    # 6. Verify Failover: The follower should have taken over
    follower_coord = await follower_sdk.resolve_system_by_type(CoordinationSystem)
    assert follower_coord.is_leader is True, f"Follower {follower_coord._node_id} failed to take over"
    
    # 7. Final Cleanup
    await follower_sdk.on_shutdown()
