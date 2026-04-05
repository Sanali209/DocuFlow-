import os
import time
from pathlib import Path

import anyio
from loguru import logger

from docuflow.application.base import BaseSystem
from docuflow.infrastructure import constants
from docuflow.infrastructure.config import Config


class HousekeepingSystem(BaseSystem):
    """Infrastructure system for cluster maintenance and garbage collection.

    This service prevents shared filesystem exhaustion by periodically
    purging stale bus messages and rotating database snapshots according
    to the defined retention policies.

    Examples:
        >>> gc = container.get(HousekeepingSystem)
        >>> # Leader node performs daily cleanup:
        >>> if coordination.is_leader:
        ...     await gc.purge_stale_messages()
        ...     await gc.rotate_snapshots()
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self._bus_path = Path(config.shared_path) / constants.BUS_DIR_NAME
        self._snapshots_path = Path(config.shared_path) / constants.SYNC_SNAPSHOTS_DIR

    async def purge_stale_messages(
        self, max_age_seconds: int = constants.GC_STALE_BUS_AGE_SECONDS
    ) -> int:
        """Remove old messages from the File Bus folders.

        Args:
            max_age_seconds: Maximum allowed age of a message before deletion.
                             Defaults to 24 hours.

        Returns:
            The number of deleted stale message files.
        """
        deleted_count = 0
        now = time.time()

        folders = [
            self._bus_path / constants.BUS_INBOX_DIR,
            self._bus_path / constants.BUS_OUTBOX_DIR,
        ]

        for folder in folders:
            if not folder.exists():
                continue

            for filename in os.listdir(folder):
                file_path = folder / filename
                if self._is_stale_file(file_path, now, max_age_seconds):
                    if await self._try_delete_file(file_path):
                        deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Housekeeping: Cleaned up {deleted_count} stale bus messages")
        return deleted_count

    async def rotate_snapshots(self, keep_count: int = constants.GC_MAX_SNAPSHOTS_TO_KEEP) -> int:
        """Keep only the most recent N snapshots to prevent storage exhaustion.

        Args:
            keep_count: The number of most recent snapshots to retain.

        Returns:
            The number of rotated (deleted) old snapshots.
        """
        if not self._snapshots_path.exists():
            return 0

        # Pattern matches snapshots (e.g., SNAP_*.json)
        pattern = f"{constants.SYNC_PREFIX_SNAP}*{constants.SYNC_EXTENSION}"
        snapshots = sorted(
            [f for f in self._snapshots_path.glob(pattern) if f.is_file()],
            key=os.path.getmtime,
        )

        if len(snapshots) <= keep_count:
            return 0

        # Identify files older than the 'keep_count' most recent ones
        to_delete = snapshots[: len(snapshots) - keep_count]
        rotated_count = 0

        for file_path in to_delete:
            if await self._try_delete_file(file_path):
                rotated_count += 1

        if rotated_count > 0:
            logger.info(f"Housekeeping: Rotated {rotated_count} old snapshots")
        return rotated_count

    # --- Private Helpers: Complexity Decomposition ---

    def _is_stale_file(self, file_path: Path, now: float, max_age: int) -> bool:
        """Determine if a file's modification time exceeds the allowed age."""
        if file_path.is_dir():
            return False

        try:
            mtime = os.path.getmtime(file_path)
            return (now - mtime) > max_age
        except OSError:
            return False

    async def _try_delete_file(self, file_path: Path) -> bool:
        """Attempt to delete a file and log any failures."""
        try:
            await anyio.Path(file_path).unlink(missing_ok=True)
            return True
        except OSError as e:
            logger.error(f"Housekeeping: Failed to delete {file_path.name}: {e}")
            return False
