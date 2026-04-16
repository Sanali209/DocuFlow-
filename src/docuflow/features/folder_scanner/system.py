import asyncio
import datetime
import hashlib
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import Engine
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    PartLibrary,
    TaskItem,
    TaskPart,
    WorkItem,
    WorkItemStatus,
    WorkItemType,
    WorkLog,
    WorkLogType,
)
from docuflow.features.folder_scanner.parsers.folder import FolderMeta, FolderNameParser
from docuflow.features.folder_scanner.parsers.gnc import GncParser
from docuflow.features.folder_scanner.parsers.svg_gen import PartPreviewGenerator
from docuflow.features.folder_scanner.parsers.task_file import TaskFileParser
from docuflow.features.folder_scanner.settings import FolderScannerSettings
from docuflow.features.inventory.system import InventorySystem
from docuflow.features.notifications.system import NotificationService
from docuflow.features.parts.system import PartLibrarySystem
from docuflow.features.projects.system import ProjectSystem
from docuflow.infrastructure.config import Config

logger = logging.getLogger(__name__)


class FolderScannerSystem(BaseSystem):
    """
    Automated ingestion engine for production folders.

    Principles:
    - Master-Only Execution: Polling loop runs only on the leader node.
    - Code as Documentation: Methods include usage examples and descriptive logic.
    """

    # Internal Scanner Constants
    LEADER_POLL_INTERVAL_SECONDS = 5
    MD5_CHUNK_SIZE = 4096

    def __init__(self, config: Config, sdk: Any, engine: Engine, admin_system: Any | None = None):
        super().__init__(config)
        self.sdk = sdk
        self.db_engine = engine
        self._admin_system = admin_system
        self._is_active_polling = False
        self._loop_task: asyncio.Task | None = None
        self._last_successful_scan: datetime.datetime | None = None
        self._items_discovered_count: int = 0

        # Compatibility attributes for tests
        self._last_scan_time: datetime.datetime | None = None
        self._files_found: int = 0

        # Ingestion Sub-parsers
        self.folder_metadata_parser = FolderNameParser()
        self.task_filename_parser = TaskFileParser()
        self.gnc_content_parser = GncParser()

        # Resource Generators
        self.preview_base_path = Path(config.shared_path) / "previews"
        self.preview_generator = PartPreviewGenerator(self.preview_base_path)

    def get_status(self, *args: Any, **kwargs: Any) -> dict:
        """Alias for get_ingestion_status for test compatibility."""
        s = self.get_ingestion_status()
        return {
            "is_active": s["is_active"],
            "is_running": s["is_active"],
            "last_scan_at": s["last_scan_at"],
            "last_scan_time": s["last_scan_at"],
            "items_found": s["items_found"],
            "files_found": s["items_found"],
        }

    @property
    def is_running(self) -> bool:
        """Alias for _is_active_polling for test compatibility."""
        return self._is_active_polling

    def get_ingestion_status(self) -> dict:
        """
        Retrieves real-time metrics of the ingestion engine.

        Example:
            status = scanner.get_ingestion_status()
            print(f"Items found: {status['items_found']}")
        """
        return {
            "is_active": self._is_active_polling,
            "last_scan_at": self._last_successful_scan,
            "items_found": self._items_discovered_count,
        }

    def get_settings(self, *args: Any, **kwargs: Any) -> FolderScannerSettings:
        """Synchronous wrapper for fetch_scanner_settings for test compatibility."""
        return self.fetch_scanner_settings()

    def fetch_scanner_settings(self) -> FolderScannerSettings:
        """Internal synchronous helper to fetch settings from AdminSystem."""

        if self._admin_system:
            data = self._admin_system.get_node_settings(self.config.node_id, "folder_scanner")
            return FolderScannerSettings(**data)
        return FolderScannerSettings()

    @property
    def _admin(self):
        """Getter for _admin_system for test compatibility."""
        return self._admin_system

    def scan_now(self, *args: Any, **kwargs: Any) -> Any:
        """Alias for trigger_manual_ingestion for test compatibility."""
        return self.trigger_manual_ingestion()

    def _scan_all(self, *args: Any, **kwargs: Any) -> Any:
        """Synchronous wrapper for run_full_scan_cycle."""
        settings = self.fetch_scanner_settings()
        if args and isinstance(args[0], FolderScannerSettings):
            settings = args[0]

        loop = asyncio.get_event_loop()
        return loop.create_task(self.run_full_scan_cycle(settings))

    @property
    def _is_master(self) -> bool:
        """Leader check for test compatibility."""
        try:
            return self.sdk.orchestrator.is_leader
        except Exception:
            return False

    def trigger_manual_ingestion(self) -> Any:
        """
        Forcefully triggers a scan cycle outside the regular poll loop.

        Example:
            scanner.trigger_manual_ingestion()
        """
        loop = asyncio.get_event_loop()
        return loop.create_task(self._trigger_manual_ingestion_async())

    async def _trigger_manual_ingestion_async(self) -> None:
        is_leader = self.sdk.orchestrator.is_leader
        if not is_leader:
            logger.warning("Ingestion: Manual trigger ignored on non-master node.")
            return

        settings = self.fetch_scanner_settings()
        if not settings.enabled:
            logger.warning("Ingestion: Scanner is disabled in global settings.")
            return

        logger.info("Ingestion: Starting manual discovery cycle.")
        await self.run_full_scan_cycle(settings)

    async def on_startup(self) -> None:
        """Starts the background leader-aware polling loop."""
        self._is_active_polling = True
        self._loop_task = asyncio.create_task(self._discovery_loop())
        logger.info("FolderScanner: Polling loop initialized.")

    async def on_shutdown(self) -> None:
        """Ceases all background ingestion activities."""
        self._is_active_polling = False
        if self._loop_task:
            self._loop_task.cancel()
        logger.info("FolderScanner: Shutting down.")

    # --- Ingestion Pipeline Logic ---

    async def _discovery_loop(self) -> None:
        """Main loop that respects cluster leadership status."""
        while self._is_active_polling:
            try:
                if not self.sdk.orchestrator.is_leader:
                    await asyncio.sleep(self.LEADER_POLL_INTERVAL_SECONDS)
                    continue

                settings = self.fetch_scanner_settings()
                if settings.enabled:
                    await self.run_full_scan_cycle(settings)

                await asyncio.sleep(settings.poll_interval_seconds)
            except Exception as error:
                logger.error(f"Ingestion: Loop error: {error}", exc_info=True)
                await asyncio.sleep(10)

    async def run_full_scan_cycle(self, settings: FolderScannerSettings) -> None:
        """
        Iterates over all configured network paths to discover new production folders.
        """
        self._items_discovered_count = 0
        self._files_found = 0  # Reset for compatibility

        # Standardize source path configurations
        discovery_targets = [
            (settings.sidra_scan_path, WorkItemType.SIDRA),
            (settings.mihtav_scan_path, WorkItemType.MIHTAV),
            (settings.other_scan_path, WorkItemType.REWORK),
        ]

        for directory_string, item_type in discovery_targets:
            if not directory_string:
                continue

            root_path = Path(directory_string)
            if root_path.exists():
                await self.scan_directory_path(root_path, item_type, settings)
            else:
                logger.error(f"Ingestion: Scan root missing: {directory_string}")

        self._last_successful_scan = datetime.datetime.now()
        self._last_scan_time = self._last_successful_scan  # For compatibility
        self._files_found = self._items_discovered_count  # For compatibility

        # Audit the scan cycle
        with Session(self.db_engine) as db_session:
            from docuflow.domain.entities.production import WorkLog, WorkLogType

            scan_log = WorkLog(
                log_type=WorkLogType.INFO,
                message=f"Scanner completed cycle. Discovered {self._items_discovered_count} items.",
                node_id=self.config.node_id,
            )
            db_session.add(scan_log)
            db_session.commit()

    async def scan_directory_path(
        self, root_path: Path, work_type: WorkItemType, settings: FolderScannerSettings
    ) -> None:
        """Iterates through subdirectories and synchronizes them with the database."""
        logger.info(f"Ingestion: Scanning root '{root_path.name}' for {work_type.value}")

        self._log_ingestion_event(f"Discovery start: {root_path.name} ({work_type.value})")

        folders_processed = 0
        for entry in root_path.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue

            folders_processed += 1
            metadata = self.folder_metadata_parser.parse(entry.name)
            work_item = await self.synchronize_work_item(entry, metadata, work_type, root_path)
            self._items_discovered_count += 1

            await self._process_folder_contents(entry, work_item, root_path)

        self._log_ingestion_event(
            f"Discovery complete: found {folders_processed} groups in {root_path.name}"
        )

    async def synchronize_work_item(
        self, folder: Path, metadata: FolderMeta, work_type: WorkItemType, root_path: Path
    ) -> WorkItem:
        """Idempotently creates or updates a WorkItem entry."""
        async with self.sdk.request_scope():
            project_sys = await self.sdk.resolve_system_by_type(ProjectSystem)
            default_project = project_sys.resolve_default_workshop_project()

            with Session(self.db_engine) as db_session:
                existing = db_session.exec(
                    select(WorkItem).where(WorkItem.folder_name == folder.name)
                ).first()
                if existing:
                    existing.last_scanned_at = datetime.datetime.now()
                    db_session.add(existing)
                    db_session.commit()
                    db_session.refresh(existing)
                    return existing

                # New WorkItem discovery
                new_item = WorkItem(
                    folder_name=folder.name,
                    folder_path=str(folder.relative_to(root_path)),
                    work_item_type=work_type,
                    sidra_number=metadata.sidra_number,
                    sidra_step=metadata.sidra_step,
                    project_id=default_project.id,
                    status=WorkItemStatus.NEW,
                    last_scanned_at=datetime.datetime.now(),
                )
                db_session.add(new_item)
                db_session.commit()
                db_session.refresh(new_item)
                return new_item

    async def _process_folder_contents(self, folder: Path, work_item: WorkItem, root_path: Path):
        """Discovers and parses GNC task files within a folder."""
        gnc_files = [
            f
            for f in folder.iterdir()
            if f.suffix.upper() == ".GNC" and not self.task_filename_parser.is_variant(f)
        ]

        if not gnc_files:
            if work_item.status != WorkItemStatus.PENDING_CUTS:
                await self._update_status(work_item, WorkItemStatus.PENDING_CUTS)
                # Notify about empty production folder
                async with self.sdk.request_scope():
                    ns = await self.sdk.resolve_system_by_type(NotificationService)
                    await ns.emit("scan.empty_folder", folder_name=folder.name)
        else:
            # Progress from pending if files were found
            if work_item.status == WorkItemStatus.PENDING_CUTS:
                await self._update_status(work_item, WorkItemStatus.NEW)

            for gnc_path in gnc_files:
                await self.process_task_file(gnc_path, work_item, root_path)

    async def process_task_file(self, gnc_path: Path, work_item: WorkItem, root_path: Path) -> None:
        """Parses a specific GNC file and synchronizes its nested tasks and parts."""
        meta = self.task_filename_parser.parse_task_filename(gnc_path.name)
        relative_path = str(gnc_path.relative_to(root_path))
        file_hash = self._calculate_file_checksum(gnc_path)

        # Check if hash changed WITHOUT keeping a session open during parsing
        with Session(self.db_engine) as db_session:
            task = db_session.exec(
                select(TaskItem).where(TaskItem.file_path == relative_path)
            ).first()
            if task and task.file_hash == file_hash:
                return  # No changes detected

        # Content changed or new file discovered
        parsed_data = self.gnc_content_parser.parse(gnc_path)
        mat_id = await self.resolve_material_mapping(parsed_data)

        with Session(self.db_engine) as db_session:
            task = db_session.exec(
                select(TaskItem).where(TaskItem.file_path == relative_path)
            ).first()
            if not task:
                task = TaskItem(
                    work_item_id=work_item.id,
                    file_name=gnc_path.name,
                    file_path=relative_path,
                    file_hash=file_hash,
                    step_index=meta.step_index,
                    batch_index=meta.batch_index,
                    sheet_x=parsed_data.sheet_x,
                    sheet_y=parsed_data.sheet_y,
                    sheet_qty=parsed_data.sheet_qty,
                    thickness=parsed_data.thickness,
                    gnc_date=parsed_data.gnc_date,
                )
                db_session.add(task)
                db_session.commit()
                db_session.refresh(task)

            # Synchronize systemic links
            task.mat_type_id = mat_id
            db_session.add(task)
            db_session.commit()  # Atomic save before parts recursion

            # Resolve parts: we will handle each part in its own atomic scope
            # to keep the code clean and thread-safe.
            # We pass only necessary IDs to ensure no session cross-contamination.
            task_id = task.id
            for part_data in parsed_data.parts:
                await self.resolve_part_mapping(part_data, task_id, mat_id)

    # --- Ingestion Helpers ---

    async def resolve_material_mapping(self, parsed_sheet) -> int | None:
        """Maps GNC material codes to the inventory catalog."""
        if not parsed_sheet.mat_code:
            return None
        async with self.sdk.request_scope():
            inventory_sys = await self.sdk.resolve_system_by_type(InventorySystem)
            mat = inventory_sys.create_material_definition(
                code=parsed_sheet.mat_code, thickness=parsed_sheet.thickness
            )
            return mat.id

    async def resolve_part_mapping(self, part_data, task_id: int, mat_id: int):
        """Maps nested parts to the global library and increments task-part counts."""
        async with self.sdk.request_scope():
            part_sys = await self.sdk.resolve_system_by_type(PartLibrarySystem)

            with Session(self.db_engine) as db_session:
                part_entry = db_session.exec(
                    select(PartLibrary).where(
                        PartLibrary.sku == part_data.sku, PartLibrary.version == part_data.version
                    )
                ).first()

            if not part_entry:
                bbox_x, bbox_y, svg_path = self.preview_generator.generate(part_data, part_data.sku)
                # This has internal commit so it's safe
                part_entry = part_sys.synchronize_part_definition(
                    sku=part_data.sku,
                    version=part_data.version,
                    mat_type_id=mat_id,
                    bbox_x=bbox_x,
                    bbox_y=bbox_y,
                    svg_preview_path=svg_path,
                    contour_count=len(part_data.contours),
                )

        # Task Link
        with Session(self.db_engine) as db_session:
            mapping = db_session.exec(
                select(TaskPart).where(
                    TaskPart.task_item_id == task_id,
                    TaskPart.part_sku == part_data.sku,
                    TaskPart.version == part_data.version,
                )
            ).first()

            if not mapping:
                mapping = TaskPart(
                    task_item_id=task_id,
                    part_sku=part_data.sku,
                    version=part_data.version,
                    qty=part_data.qty,
                    part_id=part_entry.id,
                )
                db_session.add(mapping)
                db_session.commit()

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum for file deduplication and change detection."""
        md5 = hashlib.md5()  # noqa: S324
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(self.MD5_CHUNK_SIZE), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def _log_ingestion_event(self, message: str):
        with Session(self.db_engine) as db_session:
            log = WorkLog(log_type=WorkLogType.INFO, message=message, node_id=self.config.node_id)
            db_session.add(log)
            db_session.commit()

    async def _update_status(self, work_item: WorkItem, status: WorkItemStatus):
        with Session(self.db_engine) as db_session:
            db_session.add(work_item)
            work_item.status = status
            db_session.commit()
