import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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

        filename = os.path.basename(event.src_path)
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
        >>> # Sending a request to another node
        >>> bus = container.get(FileBusSystem)
        >>> await bus.send_request("STATION_A", "CLEAN_HEAD", {"force": True})
        '1712012345678'
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
        self._observer.schedule(self._handler, str(self._inbox), recursive=False)
        self._observer.start()
        logger.info(f"FileBus: Monitoring {self._inbox} for node {self._node_id}")

    async def on_shutdown(self) -> None:
        """Gracefully stop the background file observer."""
        self._observer.stop()
        self._observer.join()
        logger.info("FileBus: Offline")

    async def send_request(
        self, target_id: str, command: str, data: Dict[str, Any]
    ) -> str:
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
        self, target_id: str, request_id: str, command: str, data: Dict[str, Any]
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

    async def poll_messages(
        self, folder: str = constants.BUS_INBOX_DIR
    ) -> List[Dict[str, Any]]:
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

    # --- Private Helpers: Complexity Decomposition ---

    def _ensure_directories_exist(self) -> None:
        """Create necessary bus folders if they are missing."""
        for path in [self._inbox, self._outbox]:
            path.mkdir(parents=True, exist_ok=True)

    def _generate_unique_id(self) -> str:
        """Generate a millisecond-precision timestamp ID."""
        return str(int(time.time() * 1000))

    def _build_filename(
        self, prefix: str, from_id: str, to_id: str, unique_id: str
    ) -> str:
        """Construct a protocol-compliant filename."""
        return (
            f"{prefix}{from_id}{constants.BUS_DELIMITER}"
            f"{to_id}{constants.BUS_DELIMITER}{unique_id}{constants.BUS_EXTENSION}"
        )

    def _build_payload(
        self, target_id: str, message_id: str, command: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
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

    def _is_relevant_message(self, filename: str, folder_name: str) -> bool:
        """Determine if a file is a finalized message addressed to this node."""
        if not filename.endswith(constants.BUS_EXTENSION):
            return False
        if filename.startswith(constants.BUS_TEMP_PREFIX):
            return False

        # Protocol check: {TYPE}_{FROM}_{TO}_{ID}.json
        # Check if current node_id is in the 'TO' position
        # We look for _{node_id}_ to account for underscores in IDs
        is_addressed_to_me = (
            f"{constants.BUS_DELIMITER}{self._node_id}{constants.BUS_DELIMITER}"
            in filename
        )

        prefix = (
            constants.BUS_PREFIX_REQ
            if folder_name == constants.BUS_INBOX_DIR
            else constants.BUS_PREFIX_RES
        )
        return is_addressed_to_me and filename.startswith(prefix)

    async def _try_read_message(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Attempt to read and parse a JSON message from disk."""
        try:
            content_bytes = await anyio.Path(file_path).read_bytes()
            return json.loads(content_bytes)
        except (json.JSONDecodeError, OSError):
            return None

    async def _atomic_write(
        self, target_dir: Path, filename: str, payload: Dict[str, Any]
    ) -> None:
        """Perform a collision-safe write using temp files and atomic rename."""
        temp_path = target_dir / f"{constants.BUS_TEMP_PREFIX}{filename}"
        final_path = target_dir / filename

        # 1. Write content to the staging (TEMP_) file
        await anyio.Path(temp_path).write_text(json.dumps(payload, indent=2))

        # 2. Rename to finalized name (Atomic on Samba/NFS targets)
        os.rename(temp_path, final_path)
