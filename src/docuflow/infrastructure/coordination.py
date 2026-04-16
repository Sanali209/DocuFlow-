import json
import os
import time
from pathlib import Path

import anyio
from loguru import logger

from docuflow.application.base import BaseSystem
from docuflow.infrastructure import constants
from docuflow.infrastructure.config import Config


class CoordinationSystem(BaseSystem):
    """Dynamic leader election system using atomic shared filesystem locks.

    This system ensures only one node in the cluster acts as the 'Leader'
    responsible for maintenance tasks (shapshotting, GC). It uses a heartbeat
    mechanism for automatic failover.

    Examples:
        >>> coordination = container.get(CoordinationSystem)
        >>> if coordination.is_leader:
        ...     await perform_maintenance()
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self._node_id = config.node_id
        self._lock_path = Path(config.shared_path) / constants.COORDINATOR_LOCK_FILE
        self._is_leader = False
        self._heartbeat_interval = config.heartbeat_interval
        self._timeout_seconds = config.coordinator_timeout
        self._stop_event = anyio.Event()

        # Cooldown period after a manual step-down to prevent immediate re-election
        self._step_down_until: float = 0.0

    @property
    def is_leader(self) -> bool:
        """Indicate if the current node is the cluster coordinator."""
        return self._is_leader

    @property
    def node_id(self) -> str:
        """The unique identifier for this node."""
        return self._node_id

    async def on_startup(self) -> None:
        """Initialize the coordination state and attempt initial election."""
        heartbeats_dir = Path(self.config.shared_path) / constants.COORDINATOR_HEARTBEATS_DIR
        logger.info(
            f"Coordination [{self._node_id}]: Mapping heartbeats to {heartbeats_dir.absolute()}"
        )
        heartbeats_dir.mkdir(parents=True, exist_ok=True)

        await self.try_become_leader()
        self._stop_event = anyio.Event()

    async def on_shutdown(self) -> None:
        """Release the leader lock and signal the heartbeat loop to stop."""
        self._stop_event.set()
        if self._is_leader:
            await self._release_lock()
            self._is_leader = False

    async def run_coordination_loop(self) -> None:
        """Background loop for leader election and heartbeat renewals.

        This method should be run as a persistent background task.
        """
        logger.info(f"Coordination: Starting heartbeat loop for {self._node_id}")
        while not self._stop_event.is_set():
            await self._emit_node_heartbeat()
            await self.try_become_leader()
            await anyio.sleep(self._heartbeat_interval)

    async def _emit_node_heartbeat(self) -> None:
        """Write node-specific status to the shared heartbeats directory."""
        heartbeats_dir = Path(self.config.shared_path) / constants.COORDINATOR_HEARTBEATS_DIR
        heartbeat_file = heartbeats_dir / f"node_{self._node_id}.json"

        payload = {
            "node_id": self._node_id,
            "is_leader": self._is_leader,
            "timestamp": time.time(),
            "last_active": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pid": os.getpid(),
        }

        try:
            # Atomic write for status files
            temp_path = heartbeat_file.with_suffix(".tmp")
            logger.trace(
                f"Coordination [{self._node_id}]: Writing heartbeat {payload['timestamp']} to {temp_path}"
            )
            await anyio.Path(temp_path).write_text(json.dumps(payload, indent=2))
            os.replace(temp_path, heartbeat_file)
            logger.trace(
                f"Coordination [{self._node_id}]: Heartbeat published (leader={self._is_leader})"
            )
        except OSError as error:
            logger.error(
                f"Coordination [{self._node_id}]: CRITICAL - Failed to emit heartbeat: {error}"
            )

    async def try_become_leader(self) -> bool:
        """Execute the leader election algorithm.

        This method attempts to acquire the shared lock file. If the lock
        is missing or stale (no heartbeat), this node will take ownership.
        If self already owns it, the heartbeat is renewed.

        This method respects the manual step-down cooldown period.

        Returns:
            True if the node is currently the Leader, False otherwise.
        """
        if time.time() < self._step_down_until:
            self._is_leader = False
            return False

        try:
            if not self._lock_path.exists():
                return await self._acquire_lock_atomically()

            lock_metadata = await self._read_lock_metadata()
            if not lock_metadata:
                return await self._acquire_lock_atomically()

            if self._is_self_owned(lock_metadata):
                await self._acquire_lock_atomically()  # Refresh heartbeat
                return True

            if self._is_lock_stale(lock_metadata):
                logger.warning(f"Coordination: Takeover from {lock_metadata.get('node_id')}")
                return await self._acquire_lock_atomically()

            self._is_leader = False
            return False

        except OSError as error:
            logger.error(f"Coordination: Election error: {error}")
            return await self._acquire_lock_atomically()

    # --- Private Helpers: Complexity Decomposition ---

    async def _read_lock_metadata(self) -> dict | None:
        """Safely read and parse the shared lock file content."""
        try:
            content = await anyio.Path(self._lock_path).read_text()
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return None

    def _is_self_owned(self, lock_metadata: dict) -> bool:
        """Check if the existing lock belongs to this current node."""
        return lock_metadata.get("node_id") == self._node_id

    def _is_lock_stale(self, lock_metadata: dict) -> bool:
        """Check if the lock owner has failed to heartbeat within the timeout."""
        last_heartbeat = lock_metadata.get("timestamp", 0)
        age = time.time() - last_heartbeat
        return age > self._timeout_seconds

    async def _acquire_lock_atomically(self) -> bool:
        """Write node metadata to a temp file and rename to the target lock.

        This ensures that multiple nodes attempting election simultaneously
        won't result in a partial or corrupted lock file.
        """
        temp_filename = (
            f"{constants.COORDINATOR_TEMP_LOCK_PREFIX}{self._node_id}"
            f"{constants.COORDINATOR_TEMP_LOCK_SUFFIX}"
        )
        temp_path = self._lock_path.with_name(temp_filename)

        payload = {
            "node_id": self._node_id,
            "timestamp": time.time(),
            "last_active": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            await anyio.Path(temp_path).write_text(json.dumps(payload, indent=2))
            os.replace(temp_path, self._lock_path)

            if not self._is_leader:
                logger.info(f"Coordination: Node {self._node_id} elected LEADER")
            self._is_leader = True
            return True
        except OSError as error:
            logger.error(f"Coordination: Failed to acquire lock: {error}")
            self._is_leader = False
            return False

    async def step_down(self, cooldown: float = 10.0) -> None:
        """Manually release leadership and enter a cooldown period.

        Args:
            cooldown: Seconds to wait before attempting re-election.
        """
        if self._is_leader:
            logger.warning(f"Coordination: Manual step-down triggered for {self._node_id}")
            await self._release_lock()
            self._is_leader = False

        self._step_down_until = time.time() + cooldown

    async def _release_lock(self) -> None:
        """Safely delete the coordinator lock file if it belongs to this node."""
        lock_metadata = await self._read_lock_metadata()
        if lock_metadata and self._is_self_owned(lock_metadata):
            await anyio.Path(self._lock_path).unlink(missing_ok=True)
            logger.info(f"Coordination: Released leader lock for {self._node_id}")
