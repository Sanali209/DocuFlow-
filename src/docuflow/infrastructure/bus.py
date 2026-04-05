import json
import os
import time
from pathlib import Path
from typing import Any

import anyio
from loguru import logger
from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from docuflow.application.base import BaseSystem
from docuflow.infrastructure import constants
from docuflow.infrastructure.config import Config


class InboxHandler(FileSystemEventHandler):
    """External file system event handler for the DocuFlow File Bus.

    This class monitors the shared filesystem and identifies new message
    arrivals. It filters out temporary staging files and non-protocol files.

    Attributes:
        system: The FileBusSystem instance to notify of new messages.
    """

    def __init__(self, system: "FileBusSystem"):
        self.system = system

    def on_created(self, event: FileCreatedEvent) -> None:
        """Triggered when a new file is detected in the monitored folder."""
        if event.is_directory:
            return

        filename = os.path.basename(os.fsdecode(event.src_path))
        if self._is_valid_new_message(filename):
            logger.debug(f"FileBus: Valid new message detected: {filename}")

    def _is_valid_new_message(self, filename: str) -> bool:
        """Check if a filename represents a finalized protocol message."""
        is_json = filename.endswith(constants.BUS_EXTENSION)
        is_not_temp = not filename.startswith(constants.BUS_TEMP_PREFIX)
        return is_json and is_not_temp


class FileBusSystem(BaseSystem):
    """Asynchronous file-based messaging bus for decentralized node clusters.

    This system provides reliable request/response semantics over high-latency
    network shares (Samba/CIFS) by using atomic write protocols and background
    polling-based monitoring.

    Examples:
        Create an instance with node configuration and use `send_request()`
        or `send_response()` from an async context.
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self._node_id = config.node_id
        self._bus_path = Path(config.shared_path) / constants.BUS_DIR_NAME
        self._inbox = self._bus_path / constants.BUS_INBOX_DIR
        self._outbox = self._bus_path / constants.BUS_OUTBOX_DIR

        # Observer tuned for network share stability
        self._observer = PollingObserver(timeout=constants.OBSERVER_POLLING_INTERVAL)
        self._handler = InboxHandler(self)

    async def on_startup(self) -> None:
        """Initialize the bus directory structure and start file monitoring."""
        self._ensure_directories_exist()
        # Cleanup any stale staging files left from previous crashes or runs
        try:
            self._cleanup_temp_files()
        except Exception:
            logger.exception("FileBus: Failed during temp-file cleanup on startup")
        self._observer.schedule(self._handler, str(self._inbox), recursive=False)
        self._observer.start()
        logger.info(f"FileBus: Monitoring {self._inbox} for node {self._node_id}")

    async def on_shutdown(self) -> None:
        """Gracefully stop the background file observer."""
        self._observer.stop()
        self._observer.join()
        logger.info("FileBus: Offline")

    async def send_request(self, target_id: str, command: str, data: dict[str, Any]) -> str:
        """Atomically deposit a request message for a target node.

        Args:
            target_id: ID of the node intended to receive the request.
            command: The specific action or verb requested.
            data: Arbitrary payload for the command.

        Returns:
            The unique ID generated for this request.
        """
        request_id = self._generate_unique_id()
        filename = self._build_filename(
            constants.BUS_PREFIX_REQ, self._node_id, target_id, request_id
        )
        payload = self._build_payload(target_id, request_id, command, data)

        await self._atomic_write(self._inbox, filename, payload)
        return request_id

    async def send_response(
        self, target_id: str, request_id: str, command: str, data: dict[str, Any]
    ) -> str:
        """Atomically deposit a response to an existing request.

        Args:
            target_id: ID of the node that sent the original request.
            request_id: The ID from the original request message.
            command: The specific action or verb being responded to.
            data: Arbitrary payload for the response.

        Returns:
            The unique ID generated for this response (matches request_id).
        """
        filename = self._build_filename(
            constants.BUS_PREFIX_RES, self._node_id, target_id, request_id
        )
        payload = self._build_payload(target_id, request_id, command, data)

        await self._atomic_write(self._outbox, filename, payload)
        return request_id

    async def poll_messages(self, folder: str = constants.BUS_INBOX_DIR) -> list[dict[str, Any]]:
        """Retrieve all finalized messages currently pending for this node.

        Args:
            folder: The bus folder to scan (INBOX or OUTBOX).

        Returns:
            A list of parsed message dictionaries, including '_filename' metadata.
        """
        target_dir = self._resolve_folder_path(folder)
        if not target_dir.exists():
            return []

        received_messages = []
        for filename in os.listdir(target_dir):
            if not self._is_relevant_message(filename, folder):
                continue

            message_data = await self._try_read_message(target_dir / filename)
            if message_data:
                message_data["_filename"] = filename
                received_messages.append(message_data)

        return received_messages

    async def delete_message(self, folder: str, filename: str) -> None:
        """Permanently remove a processed message from the shared folder."""
        target_dir = self._resolve_folder_path(folder)
        file_path = target_dir / filename
        await anyio.Path(file_path).unlink(missing_ok=True)

    async def write_message(self, payload: dict[str, Any]) -> str:
        """Write a raw P2P envelope for orchestrator-level broadcasts.

        Returns:
            The generated protocol message id used in the filename.
        """
        message_id = self._generate_unique_id()
        filename = self._build_broadcast_filename(self._node_id, message_id)
        await self._atomic_write(self._inbox, filename, payload)
        return message_id

    # --- Private Helpers: Complexity Decomposition ---

    def _ensure_directories_exist(self) -> None:
        """Create necessary bus folders if they are missing."""
        for path in [self._inbox, self._outbox]:
            path.mkdir(parents=True, exist_ok=True)

    def _generate_unique_id(self) -> str:
        """Generate a millisecond-precision timestamp ID."""
        return str(int(time.time() * 1000))

    def _build_broadcast_filename(self, from_id: str, unique_id: str) -> str:
        """Construct a broadcast filename visible to all nodes."""
        return (
            f"{constants.BUS_PREFIX_BROADCAST}{from_id}"
            f"{constants.BUS_DELIMITER}{unique_id}{constants.BUS_EXTENSION}"
        )

    def _build_filename(self, prefix: str, from_id: str, to_id: str, unique_id: str) -> str:
        """Construct a protocol-compliant filename."""
        return (
            f"{prefix}{from_id}{constants.BUS_DELIMITER}"
            f"{to_id}{constants.BUS_DELIMITER}{unique_id}{constants.BUS_EXTENSION}"
        )

    def _build_payload(
        self, target_id: str, message_id: str, command: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Construct the standard JSON message structure."""
        return {
            "header": {
                "from": self._node_id,
                "to": target_id,
                "id": message_id,
                "cmd": command,
                "timestamp": time.time(),
            },
            "body": data,
        }

    def _resolve_folder_path(self, folder_name: str) -> Path:
        """Map a folder type string to an absolute path."""
        return self._inbox if folder_name == constants.BUS_INBOX_DIR else self._outbox

    def _cleanup_temp_files(self, older_than_seconds: int | None = None) -> None:
        """Remove TEMP_* files older than `older_than_seconds` from bus folders.

        This is a best-effort cleanup invoked at startup to avoid littering the
        shared bus with abandoned staging files that may confuse consumers.
        """
        if older_than_seconds is None:
            # Prefer configured value from runtime Config, fall back to constant.
            try:
                older_than_seconds = int(self.config.bus_temp_cleanup_age_seconds)
            except Exception:
                older_than_seconds = constants.GC_STALE_BUS_AGE_SECONDS

        now = time.time()
        examined = 0
        removed = 0
        for folder in (self._inbox, self._outbox):
            try:
                if not folder.exists():
                    continue
                for entry in folder.iterdir():
                    if not entry.is_file():
                        continue
                    name = entry.name
                    if not name.startswith(constants.BUS_TEMP_PREFIX):
                        continue
                    examined += 1
                    try:
                        mtime = entry.stat().st_mtime
                        age = now - mtime
                        if age >= older_than_seconds:
                            entry.unlink(missing_ok=True)
                            removed += 1
                            logger.warning(f"FileBus: Removed stale temp file: {entry}")
                    except Exception:
                        logger.exception(f"FileBus: Error checking/removing temp file {entry}")
            except Exception:
                logger.exception(f"FileBus: Failed to scan folder for temp files: {folder}")

        logger.debug(f"FileBus: Temp cleanup examined={examined} removed={removed}")

    def _is_relevant_message(self, filename: str, folder_name: str) -> bool:
        """Determine if a file is a finalized message addressed to this node."""
        if not filename.endswith(constants.BUS_EXTENSION):
            return False
        if filename.startswith(constants.BUS_TEMP_PREFIX):
            return False

        if folder_name == constants.BUS_INBOX_DIR and filename.startswith(
            constants.BUS_PREFIX_BROADCAST
        ):
            return True

        # Protocol check: {TYPE}_{FROM}_{TO}_{ID}.json
        # Check if current node_id is in the 'TO' position
        # We look for _{node_id}_ to account for underscores in IDs
        is_addressed_to_me = (
            f"{constants.BUS_DELIMITER}{self._node_id}{constants.BUS_DELIMITER}" in filename
        )

        prefix = (
            constants.BUS_PREFIX_REQ
            if folder_name == constants.BUS_INBOX_DIR
            else constants.BUS_PREFIX_RES
        )
        return is_addressed_to_me and filename.startswith(prefix)

    async def _try_read_message(self, file_path: Path) -> dict[str, Any] | None:
        """Attempt to read and parse a JSON message from disk."""
        try:
            content_bytes = await anyio.Path(file_path).read_bytes()
            return json.loads(content_bytes)
        except (json.JSONDecodeError, OSError):
            return None

    async def _atomic_write(self, target_dir: Path, filename: str, payload: dict[str, Any]) -> None:
        """Perform a collision-safe write using temp files and atomic rename."""
        temp_path = target_dir / f"{constants.BUS_TEMP_PREFIX}{filename}"
        final_path = target_dir / filename

        # 1. Write content to the staging (TEMP_) file using binary write,
        #    flush and fsync to ensure data hits the underlying storage.
        data = json.dumps(payload, indent=2).encode("utf-8")

        try:
            # Use a blocking file write here to be able to call flush/fsync.
            with open(temp_path, "wb") as f:
                f.write(data)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    # fsync may fail on certain filesystems or permissions;
                    # still attempt the atomic replace but log the condition.
                    logger.debug(f"FileBus: os.fsync failed for {temp_path}")

            # 2. Atomically replace (safer than rename across platforms)
            os.replace(temp_path, final_path)
            logger.debug(f"FileBus: Wrote message to {final_path}")
        except Exception:
            # Best-effort cleanup of temp file to avoid littering shared folder
            try:
                if temp_path.exists():
                    os.remove(temp_path)
            except OSError:
                logger.exception(f"FileBus: Failed to remove temp file {temp_path}")
            raise
