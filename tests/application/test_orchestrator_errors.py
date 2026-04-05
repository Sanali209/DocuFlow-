from unittest.mock import AsyncMock, MagicMock

import anyio
import pytest

from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.infrastructure.config import Config


@pytest.mark.anyio
async def test_orchestrator_failure_propagation():
    """TDD: Verify that a failure in one worker triggers a full orchestrator shutdown.

    This test ensures the 'Shutdown on Failure' requirement (Task 3.2) is met,
    protecting the cluster from inconsistent states if a sync loop crashes.
    """
    config = Config(node_id="FAIL_NODE", shared_path="./tmp/fail_test")
    # Speed up intervals for the test
    config.bus_poll_interval = 0.01
    config.sync_check_interval = 0.01

    coordination = MagicMock()
    coordination.run_coordination_loop = AsyncMock()
    coordination.is_leader = True

    bus = MagicMock()
    bus.poll_messages = AsyncMock(return_value=[])

    sync = MagicMock()
    # This will trigger the failure in the maintenance worker
    sync.create_master_snapshot = AsyncMock(side_effect=RuntimeError("Simulated Sync Failure"))

    housekeeping = MagicMock()
    housekeeping.purge_stale_messages = AsyncMock()
    housekeeping.rotate_snapshots = AsyncMock()

    orchestrator = P2POrchestrator(config, coordination, bus, sync, housekeeping)

    # We need to run the orchestrator in a background task
    async with anyio.create_task_group() as tg:
        tg.start_soon(orchestrator.on_startup)

        # Wait for the failure to propagate
        await anyio.sleep(0.1)

        # Verify orchestrator is no longer running
        assert orchestrator.is_running is False

        # Ensure cleanup was attempted
        assert sync.create_master_snapshot.called
