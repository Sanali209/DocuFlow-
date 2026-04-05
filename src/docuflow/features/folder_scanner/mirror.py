import asyncio
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy import Engine
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    TaskItem,
    WorkerBucketEntry,
    WorkItem,
    WorkItemType,
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

    def __init__(self, config: Config, sdk: Any, engine: Engine):
        """
        Initialize the network synchronization service.

        Args:
            config: System configuration.
            sdk: SDK facade.
            engine: SQLAlchemy database engine.
        """
        super().__init__(config)
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

    async def _mirror_loop(self) -> None:
        """Periodic polling of the node's task bucket."""
        while self._running:
            try:
                settings = await self.sdk.resolve_system_by_type(FolderScannerSettings)
                if settings.local_ns_path:
                    await self._sync_bucket(settings)
            except Exception as e:
                logger.error(f"Error in NS Mirror loop: {e}", exc_info=True)

            # Use interval from settings
            settings = await self.sdk.resolve_system_by_type(FolderScannerSettings)
            await asyncio.sleep(settings.ns_mirror_interval_seconds)

    async def _sync_bucket(self, settings: FolderScannerSettings) -> None:
        """Fetch tasks in bucket and mirror them."""
        # 1. Get entries for this node
        with Session(self.db_engine) as db_session:
            entries = db_session.exec(
                select(WorkerBucketEntry).where(WorkerBucketEntry.node_id == self.config.node_id)
            ).all()

            active_tasks = []
            for entry in entries:
                task = db_session.get(TaskItem, entry.task_item_id)
                if task:
                    active_tasks.append(task)
                    await self._mirror_task(task, settings, db_session)

            # Commit mutations to persist logs
            db_session.commit()

    async def _mirror_task(
        self, task: TaskItem, settings: FolderScannerSettings, session: Session
    ) -> None:
        """Ensure a single task is correctly mirrored."""
        # 1. Resolve source path
        src_path = self._resolve_source_path(task, settings, session)
        if not src_path or not src_path.exists():
            logger.error(f"Source file not found for task {task.file_name}: {src_path}")
            return

        # 2. Resolve destination path (preserving hierarchy)
        # destination = local_ns_path / relative_path_from_scan_root
        dst_path = Path(settings.local_ns_path) / task.file_path

        # 3. Check if update is needed
        if not dst_path.exists():
            await self._copy_file(src_path, dst_path, settings.ns_mirror_copy_timeout_s)
            self._log_event(task, f"Copied to NS: {task.file_name}", session)
            return

        # 4. Content Verification (MD5)
        # We check network MD5 vs local MD5
        local_md5 = self._calculate_md5(dst_path)
        if task.file_hash and local_md5 != task.file_hash:
            # Significant hash change detected!
            logger.warning(f"MD5 Mismatch for {task.file_name}: Network MD5 has changed.")
            self._log_event(
                task,
                "⚠️ Сетевой файл обновился. Локальная копия устарела!",
                session,
                log_type=WorkLogType.FILE_CHANGED,
            )
            # Note: We do NOT overwrite automatically to avoid CNC reading conflicts.

    async def _copy_file(self, src: Path, dst: Path, timeout: float) -> None:
        """Perform a thread-safe copy with timeout."""

        def _do_copy():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        try:
            await asyncio.wait_for(asyncio.to_thread(_do_copy), timeout=timeout)
        except TimeoutError:
            logger.error(f"Timeout mirroring file {src} -> {dst}")
        except Exception as e:
            logger.error(f"Failed to mirror file: {e}")

    def _resolve_source_path(
        self, task: TaskItem, settings: FolderScannerSettings, session: Session
    ) -> Path | None:
        """Determine absolute network path for a relative TaskItem.file_path."""
        # Get WorkItem to know the type
        wi = session.get(WorkItem, task.work_item_id)
        if not wi:
            return None

        # Map type to configured scan root
        scan_root_str = None
        if wi.work_item_type == WorkItemType.SIDRA:
            scan_root_str = settings.sidra_scan_path
        elif wi.work_item_type == WorkItemType.MIHTAV:
            scan_root_str = settings.mihtav_scan_path
        elif wi.work_item_type == WorkItemType.REWORK:
            scan_root_str = settings.other_scan_path

        if not scan_root_str:
            # Fallback to shared_path if specific root not found
            scan_root_str = self.config.shared_path

        return Path(scan_root_str) / task.file_path

    def _calculate_md5(self, path: Path) -> str:
        """Calculate MD5 checksum for file deduplication and change detection.
        
        Note: MD5 is used here only for fast file comparison and deduplication,
        not for cryptographic security. For this use case, MD5 is acceptable.
        """
        h = hashlib.md5()  # noqa: S324
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def _log_event(
        self,
        task: TaskItem,
        message: str,
        db_session: Session,
        log_type: WorkLogType = WorkLogType.NS_MIRROR,
    ):
        log = WorkLog(
            task_item_id=task.id,
            work_item_id=task.work_item_id,
            log_type=log_type,
            message=message,
            node_id=self.config.node_id,
        )
        db_session.add(log)
        db_session.flush()
