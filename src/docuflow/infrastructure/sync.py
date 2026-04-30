import datetime
import json
from pathlib import Path
from typing import Any

import anyio
from loguru import logger
from sqlmodel import Session, SQLModel, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.identity import NodeSetting, Role, User, Workplace
from docuflow.domain.entities.production import TaskItem, WorkItem
from docuflow.infrastructure import constants
from docuflow.infrastructure.config import Config


class DataSyncSystem(BaseSystem):
    """Infrastructure system for symmetric database synchronization.

    This service ensures data consistency across the node cluster by
    capturing local state as JSON snapshots and merging remote data
    using a 'Last-Write-Wins' (LWW) conflict resolution policy.

    Examples:
        >>> sync = container.get(DataSyncSystem)
        >>> # As Leader:
        >>> snap_path = await sync.create_master_snapshot()
        >>> # As Peer:
        >>> await sync.apply_remote_snapshot(snap_path)
    """

    def __init__(self, config: Config, engine: Any) -> None:
        super().__init__(config)
        self._engine: Any = engine
        self._node_id: str = config.node_id
        self._snapshots_dir: Path = Path(config.shared_path) / constants.SYNC_SNAPSHOTS_DIR
        self._orchestrator: Any | None = None

        # Registry of domain entities involved in synchronization
        self._sync_registry: list[type[SQLModel]] = [
            NodeSetting,
            WorkItem,
            TaskItem,
            Workplace,
            Role,
            User,
        ]

    async def create_master_snapshot(self) -> Path:
        """Capture the current local database state into a shared JSON snapshot.

        Returns:
            The absolute Path to the newly created snapshot file.
        """
        self._ensure_snapshots_dir_exists()

        timestamp: str = datetime.datetime.now().isoformat().replace(":", "-")
        filename: str = (
            f"{constants.SYNC_PREFIX_SNAP}{self._node_id}_{timestamp}{constants.SYNC_EXTENSION}"
        )
        target_path: Path = self._snapshots_dir / filename

        captured_data: dict[str, list[dict[str, Any]]] = await self._gather_registry_data()
        await self._write_snapshot_atomically(target_path, captured_data)

        logger.info(f"DataSync: Created master snapshot {filename}")
        return target_path

    async def apply_remote_snapshot(self, snapshot_path: Path) -> None:
        """Merge a remote snapshot into the local database.

        Args:
            snapshot_path: Path to the remote .json snapshot file.
        """
        if not snapshot_path.exists():
            logger.error(f"DataSync: Snapshot file missing: {snapshot_path}")
            return

        snapshot_content: str = await anyio.Path(snapshot_path).read_text()
        snapshot_data: Any = json.loads(snapshot_content)

        await anyio.to_thread.run_sync(self._merge_snapshot_data, snapshot_data)  # type: ignore[attr-defined]
        logger.info(f"DataSync: Applied snapshot {snapshot_path.name}")

    def set_orchestrator(self, orchestrator: Any) -> None:
        """Inject the orchestrator to allow for delta-broadcasting.

        Required to avoid circular dependencies during DI container boot.
        """
        self._orchestrator = orchestrator

    async def broadcast_entity_update(self, entity: SQLModel) -> None:
        """Leader-only: Broadcast a single entity change to all nodes via the File Bus.

        Args:
            entity: The SQLModel instance that was modified.
        """
        if not self._orchestrator:
            logger.warning("DataSync: Orchestrator not set, cannot broadcast update.")
            return

        from docuflow.domain.messages import CommandType

        # We use UPSERT_USER as a generic placeholder or dynamic mapping for Iteration 3
        # In a full system, we'd map type(entity) to a specific command.
        data: dict[str, Any] = entity.model_dump()
        # Ensure datetime is serializable
        key: str
        val: Any
        for key, val in data.items():
            if isinstance(val, datetime.datetime):
                data[key] = val.isoformat()

        logger.info(
            f"DataSync: Broadcasting delta for {type(entity).__name__} "
            f"(ID: {getattr(entity, 'id', 'unknown')})"
        )
        await self._orchestrator.broadcast_command(CommandType.UPSERT_USER, data)

    # --- Private Helpers: Complexity Decomposition ---

    def _ensure_snapshots_dir_exists(self) -> None:
        """Create the shared snapshots folder if it is missing."""
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)

    async def _gather_registry_data(self) -> dict[str, list[dict[str, Any]]]:
        """Extract all registry-defined entities from the local database."""

        def _sync_extract() -> dict[str, list[dict[str, Any]]]:
            data_map: dict[str, list[dict[str, Any]]] = {}
            with Session(self._engine) as session:
                entity_cls: type[SQLModel]
                for entity_cls in self._sync_registry:
                    table_name: Any = entity_cls.__tablename__
                    records: Any = session.exec(select(entity_cls)).all()
                    data_map[table_name] = [r.model_dump() for r in records]
            return data_map

        return await anyio.to_thread.run_sync(_sync_extract)  # type: ignore[attr-defined]

    async def _write_snapshot_atomically(self, path: Path, data: dict) -> None:
        """Serialize data to JSON using temp+rename for crash safety.

        Writes to a TEMP_ staging file first, then atomically replaces the
        target via os.replace. If the write fails, the original file is untouched.
        """
        import os

        def _json_serial(obj: Any) -> Any:
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} is not serializable")

        serialized_json: str = json.dumps(data, default=_json_serial, indent=2)
        temp_path: Path = path.with_name(f"TEMP_{path.name}")
        try:
            await anyio.Path(temp_path).write_text(serialized_json)
            os.replace(temp_path, path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise

    def _merge_snapshot_data(self, snapshot_data: dict) -> None:
        """Internal synchronous logic for database merging."""
        with Session(self._engine) as session:
            entity_cls: type[SQLModel]
            for entity_cls in self._sync_registry:
                table_name: Any = entity_cls.__tablename__
                remote_rows: Any = snapshot_data.get(table_name, [])

                if not remote_rows:
                    continue

                pk_names: list[str] = [c.name for c in entity_cls.__table__.primary_key]  # type: ignore[attr-defined]

                row_dict: dict
                for row_dict in remote_rows:
                    self._process_remote_row(session, entity_cls, row_dict, pk_names)

            session.commit()

    def _process_remote_row(
        self, session: Session, entity_cls: type[SQLModel], row_data: dict, pk_names: list[str]
    ) -> None:
        """Process an individual remote record and resolve local conflicts."""
        row_copy: dict[str, Any] = dict(row_data)
        key: str
        value: Any
        # Cheap ISO 8601 date pre-filter (YYYY-MM-DD…) before attempting full parse.
        for key, value in row_copy.items():
            if (
                isinstance(value, str)
                and len(value) >= 10
                and value[4:5] == "-"
                and value[7:8] == "-"
            ):
                try:
                    row_copy[key] = datetime.datetime.fromisoformat(value)
                except ValueError:
                    pass

        remote_obj: SQLModel = entity_cls.model_validate(row_copy)

        pk_values: tuple[Any, ...] = tuple(getattr(remote_obj, pk) for pk in pk_names)
        local_obj: SQLModel | None = session.get(entity_cls, pk_values)

        if not local_obj:
            session.add(remote_obj)
        elif self._is_remote_newer(remote_obj, local_obj):
            self._update_local_stale_record(local_obj, row_copy)

    def _is_remote_newer(self, remote_obj: Any, local_obj: Any) -> bool:
        """Determine if a remote object has a more recent update timestamp."""
        return remote_obj.updated_at > local_obj.updated_at

    def _update_local_stale_record(self, local_obj: Any, row_data: dict) -> None:
        """Apply remote dictionary fields to an existing local object."""
        key: str
        value: Any
        for key, value in row_data.items():
            setattr(local_obj, key, value)
