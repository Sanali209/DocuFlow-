import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

import anyio
from sqlalchemy import Engine
from sqlmodel import Session, col, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    TaskItem,
    WorkerBucketEntry,
    WorkLog,
    WorkLogType,
)
from docuflow.features.folder_scanner.settings import FolderScannerSettings
from docuflow.infrastructure.config import Config

logger = logging.getLogger(__name__)


class NSMirrorService(BaseSystem):
    """
    Service that mirrors GNC files from the network share to a local folder
    (NS) for CNC automation. Unlike the scanner, this runs on all nodes.

    Preserves the directory structure of the work orders.
    """

    def __init__(
        self, config: Config, sdk: Any, engine: Engine, session: Session | None = None
    ) -> None:
        super().__init__(config, session)
        self.sdk = sdk
        self.db_engine = engine
        self._running = False
        self._task: asyncio.Task | None = None

    async def on_startup(self) -> None:
        """Start the mirroring loop."""
        self._running = True
        self._task = asyncio.create_task(self._mirror_loop())
        logger.info(f"NSMirrorService started on node {self.config.node_id}")

    async def on_shutdown(self) -> None:
        """Stop the mirroring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("NSMirrorService shut down.")

    _default_mirror_interval: float = 30.0

    async def _mirror_loop(self) -> None:
        """Periodic polling of the node's task bucket."""
        while self._running:
            interval: float = self._default_mirror_interval
            try:
                settings: FolderScannerSettings = await self.sdk.resolve_system_by_type(
                    FolderScannerSettings
                )
                interval = settings.ns_mirror_interval_seconds
                if settings.local_ns_path:
                    await self._sync_bucket(settings)
            except Exception as e:
                logger.error(f"Error in NS Mirror loop: {e}", exc_info=True)

            await asyncio.sleep(interval)

    async def on_bucket_add(self, bucket_entry: Any) -> None:
        logger.debug(f"NSMirrorService.on_bucket_add called (not implemented): {bucket_entry}")

    def _db_load_bucket_tasks(self, node_id: str) -> list[TaskItem]:
        """Sync: load all TaskItems for this node's bucket entries in one JOIN query."""
        with Session(self.db_engine) as session:
            return list(
                session.exec(
                    select(TaskItem)
                    .join(
                        WorkerBucketEntry,
                        col(TaskItem.id) == col(WorkerBucketEntry.task_item_id),
                    )
                    .where(col(WorkerBucketEntry.node_id) == node_id)
                ).all()
            )

    def _db_commit_logs(self, logs: list[WorkLog]) -> None:
        """Sync: persist a batch of WorkLog entries."""
        if not logs:
            return
        with Session(self.db_engine) as session:
            for log in logs:
                session.add(log)
            session.commit()

    async def _sync_bucket(self, settings: FolderScannerSettings) -> None:
        """Fetch tasks in bucket and mirror them."""
        active_tasks: list[TaskItem] = await anyio.to_thread.run_sync(  # type: ignore[attr-defined]
            self._db_load_bucket_tasks, self.config.node_id
        )

        pending_logs: list[WorkLog] = []
        task: TaskItem
        for task in active_tasks:
            try:
                task_logs: list[WorkLog] = await self._mirror_task(task, settings)
                pending_logs.extend(task_logs)
            except Exception as exc:
                logger.error(
                    f"NSMirrorService: failed to mirror task {task.file_name}: {exc}",
                    exc_info=True,
                )

        if pending_logs:
            await anyio.to_thread.run_sync(self._db_commit_logs, pending_logs)  # type: ignore[attr-defined]

    async def _mirror_task(self, task: TaskItem, settings: FolderScannerSettings) -> list[WorkLog]:
        """Ensure a single task is correctly mirrored. Returns WorkLog entries to persist."""
        logs: list[WorkLog] = []

        src_path: Path | None = self._resolve_source_path_no_session(task, settings)
        if not src_path or not src_path.exists():
            logger.error(f"Source file not found for task {task.file_name}: {src_path}")
            return logs

        dst_path: Path = Path(settings.local_ns_path) / task.file_path

        if not dst_path.exists():
            await self._copy_file(src_path, dst_path, settings.ns_mirror_copy_timeout_s)
            logs.append(self._make_log(task, f"Copied to NS: {task.file_name}"))
            return logs

        local_md5: str = await anyio.to_thread.run_sync(self._calculate_md5, dst_path)  # type: ignore[attr-defined]
        if task.file_hash and local_md5 != task.file_hash:
            logger.warning(f"MD5 Mismatch for {task.file_name}: Network MD5 has changed.")
            logs.append(
                self._make_log(
                    task,
                    "⚠️ Сетевой файл обновился. Локальная копия устарела!",
                    log_type=WorkLogType.FILE_CHANGED,
                )
            )

        return logs

    async def _copy_file(self, src: Path, dst: Path, timeout: float) -> None:
        """Perform a thread-safe copy with timeout."""

        def _do_copy() -> None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        try:
            await asyncio.wait_for(asyncio.to_thread(_do_copy), timeout=timeout)
        except TimeoutError:
            logger.error(f"Timeout mirroring file {src} -> {dst}")
        except Exception as e:
            logger.error(f"Failed to mirror file: {e}")

    def _resolve_source_path_no_session(
        self, task: TaskItem, settings: FolderScannerSettings
    ) -> Path | None:
        """Determine network path for a TaskItem (uses already-loaded task, no DB needed)."""
        roots: list[str | None] = [
            settings.sidra_scan_path,
            settings.mihtav_scan_path,
            settings.other_scan_path,
            self.config.shared_path,
        ]
        for root in roots:
            if root:
                candidate = Path(root) / task.file_path
                if candidate.exists():
                    return candidate
        return None

    def _make_log(
        self,
        task: TaskItem,
        message: str,
        log_type: WorkLogType = WorkLogType.NS_MIRROR,
    ) -> WorkLog:
        """Create a WorkLog entry (not yet persisted)."""
        return WorkLog(
            task_item_id=task.id,
            work_item_id=task.work_item_id,
            log_type=log_type,
            message=message,
            node_id=self.config.node_id,
        )

    def _calculate_md5(self, path: Path) -> str:
        """Calculate MD5 checksum for file deduplication and change detection.

        Delegates to the shared infrastructure utility.
        Called via anyio.to_thread.run_sync to avoid blocking the event loop.
        """
        from docuflow.infrastructure.file_utils import calculate_file_md5

        return calculate_file_md5(path)
