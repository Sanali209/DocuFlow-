from collections.abc import AsyncIterable

from dishka import AsyncContainer, Provider, Scope, provide
from loguru import logger
from sqlalchemy import Engine, event
from sqlmodel import Session, create_engine

from docuflow.application.bus.dispatcher import SecureDispatcher
from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.features.admin.system import AdminSyncSystem, AdminSystem
from docuflow.features.analytics.system import AnalyticsSystem
from docuflow.features.auth.system import AuthSystem
from docuflow.features.chat.incidents import IncidentSystem
from docuflow.features.chat.system import ChatSystem
from docuflow.features.consumables.system import ConsumableSystem
from docuflow.features.core.search import SearchSystem
from docuflow.features.folder_scanner.mirror import NSMirrorService
from docuflow.features.folder_scanner.settings import FolderScannerSettings
from docuflow.features.folder_scanner.system import FolderScannerSystem
from docuflow.features.inventory.system import InventorySystem
from docuflow.features.notifications.system import NotificationService
from docuflow.features.parts.system import PartLibrarySystem
from docuflow.features.production.system import ProductionSystem
from docuflow.features.projects.system import ProjectSystem
from docuflow.features.reports.system import ReportRegistry, ReportSystem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.view_presets.system import ViewPresetSystem
from docuflow.features.work_items.system import WorkItemSystem
from docuflow.infrastructure.bus import FileBusSystem
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.coordination import CoordinationSystem
from docuflow.infrastructure.housekeeping import HousekeepingSystem
from docuflow.infrastructure.security import HMACSigner
from docuflow.infrastructure.sync import DataSyncSystem
from docuflow.sdk import SDK


class AppProvider(Provider):
    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    @provide(scope=Scope.REQUEST)
    def get_search_system(self, session: Session) -> SearchSystem:
        """Provide global search system."""
        return SearchSystem(session)

    @provide(scope=Scope.REQUEST)
    def get_projects_system(self, config: Config, session: Session) -> ProjectSystem:
        """Provide project management system."""
        return ProjectSystem(config, session)

    @provide(scope=Scope.REQUEST)
    def get_parts_system(self, config: Config, session: Session) -> PartLibrarySystem:
        """Provide part library system."""
        return PartLibrarySystem(config, session)

    @provide(scope=Scope.REQUEST)
    def get_consumable_system(self, config: Config, session: Session, sdk: SDK) -> ConsumableSystem:
        """Provide consumable management system."""
        return ConsumableSystem(config, session, sdk)

    @provide(scope=Scope.REQUEST)
    def get_production_system(self, config: Config, session: Session, sdk: SDK) -> ProductionSystem:
        """Provide production and logistics system."""
        return ProductionSystem(config, session, sdk)

    @provide(scope=Scope.APP)
    def get_config(self) -> Config:
        """Provide application configuration."""
        return self.config

    @provide(scope=Scope.APP)
    def get_signer(self) -> HMACSigner:
        """Provide HMAC signer for message authentication."""
        return HMACSigner(self.config.storage_secret)

    @provide(scope=Scope.APP)
    def get_engine(self, config: Config) -> Engine:
        """Provide SQLAlchemy engine for node-specific database with SQLite optimizations.

        Performance Tuning:
        - journal_mode=WAL: Allows concurrent readers and a single writer.
        - synchronous=NORMAL: Reduces disk I/O while maintaining safety in WAL mode.
        - busy_timeout=30000: Wait up to 30s for locked database.
        """
        db_file = f"{config.node_id}.db"
        sqlite_url = f"sqlite:///{db_file}"
        logger.info(f"Identity [{config.node_id}]: Initialized local database at {sqlite_url}")

        engine = create_engine(
            sqlite_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,  # 30 seconds busy timeout
            },
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Apply performance-tuning PRAGMAs to each new SQLite connection."""
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            except Exception as e:
                logger.warning(f"Failed to set SQLite pragmas: {e}")
            finally:
                cursor.close()

        return engine

    @provide(scope=Scope.REQUEST)
    async def get_session(self, engine: Engine) -> AsyncIterable[Session]:
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    @provide(scope=Scope.APP)
    def get_coordination(self, config: Config) -> CoordinationSystem:
        """Provide distributed coordination system for leader election."""
        return CoordinationSystem(config)

    @provide(scope=Scope.APP)
    def get_bus(self, config: Config) -> FileBusSystem:
        """Provide file-based message bus for P2P communication."""
        return FileBusSystem(config)

    @provide(scope=Scope.APP)
    def get_sync(self, config: Config, engine: Engine) -> DataSyncSystem:
        """Provide database synchronization system."""
        return DataSyncSystem(config, engine)

    @provide(scope=Scope.APP)
    def get_housekeeping(self, config: Config) -> HousekeepingSystem:
        """Provide housekeeping system for garbage collection."""
        return HousekeepingSystem(config)

    @provide(scope=Scope.APP)
    def get_admin_sync(self, engine: Engine) -> AdminSyncSystem:
        """Provide admin synchronization system for P2P commands."""
        return AdminSyncSystem(engine)

    @provide(scope=Scope.APP)
    def get_dispatcher(self, config: Config, signer: HMACSigner) -> SecureDispatcher:
        """Provide secure message dispatcher with HMAC verification."""
        return SecureDispatcher(config, signer)

    @provide(scope=Scope.APP)
    def get_orchestrator(
        self,
        config: Config,
        coordination: CoordinationSystem,
        bus: FileBusSystem,
        sync: DataSyncSystem,
        housekeeping: HousekeepingSystem,
        dispatcher: SecureDispatcher,
        signer: HMACSigner,
        admin_sync: AdminSyncSystem,
    ) -> P2POrchestrator:
        """Provide P2P orchestrator for cluster coordination."""
        return P2POrchestrator(
            config, coordination, bus, sync, housekeeping, dispatcher, signer, admin_sync
        )

    @provide(scope=Scope.APP)
    def get_sdk(self, container: AsyncContainer) -> SDK:
        """Provide SDK facade for application layer."""
        # Cache SDK on the provider instance to guard against accidental
        # multiple instantiations outside of Dishka's scope handling.
        if hasattr(self, "_sdk") and self._sdk is not None:
            return self._sdk
        self._sdk = SDK(container)
        # Lightweight logging for diagnostics
        try:
            logger.debug(f"AppProvider: created SDK instance id={id(self._sdk)}")
        except Exception as e:
            # Loguru import failed - continue without debug logging
            import sys

            print(f"Warning: SDK debug logging unavailable: {e}", file=sys.stderr)
        return self._sdk

    @provide(scope=Scope.REQUEST)
    def get_analytics_system(self, config: Config, session: Session) -> AnalyticsSystem:
        """Provide analytics system."""
        return AnalyticsSystem(config, session)

    @provide(scope=Scope.REQUEST)
    def get_auth_service(self, config: Config, session: Session) -> AuthSystem:
        """Provide authentication service."""
        return AuthSystem(config, session)

    @provide(scope=Scope.REQUEST)
    def get_work_item_system(self, config: Config, session: Session, sdk: SDK) -> WorkItemSystem:
        """Provide work item management system."""
        return WorkItemSystem(config, session, sdk)

    @provide(scope=Scope.REQUEST)
    def get_view_preset_system(self, config: Config, session: Session) -> ViewPresetSystem:
        """Provide view preset management system."""
        return ViewPresetSystem(config, session)

    @provide(scope=Scope.REQUEST)
    def get_inventory_system(self, config: Config, session: Session, sdk: SDK) -> InventorySystem:
        """Provide inventory management system."""
        return InventorySystem(config, session, sdk)

    @provide(scope=Scope.REQUEST)
    def get_admin_system(
        self, session: Session, orchestrator: P2POrchestrator, signer: HMACSigner, config: Config
    ) -> AdminSystem:
        """Provide admin system for cluster management."""
        return AdminSystem(session, orchestrator, signer, config)

    @provide(scope=Scope.APP)
    def get_folder_scanner(self, config: Config, sdk: SDK, engine: Engine) -> FolderScannerSystem:
        """Provide folder scanner system for production task ingestion."""
        return FolderScannerSystem(config, sdk, engine)

    @provide(scope=Scope.APP)
    def get_ns_mirror(self, config: Config, sdk: SDK, engine: Engine) -> NSMirrorService:
        """Provide NS mirror service for CNC file synchronization."""
        return NSMirrorService(config, sdk, engine)

    @provide(scope=Scope.REQUEST)
    def get_notifications(self, config: Config, session: Session) -> NotificationService:
        """Provide notification service for cluster events."""
        return NotificationService(config, session)

    @provide(scope=Scope.APP)
    def get_scanner_settings(self) -> FolderScannerSettings:
        """Provide folder scanner settings schema."""
        return FolderScannerSettings()

    @provide(scope=Scope.REQUEST)
    def get_task_board(
        self,
        config: Config,
        session: Session,
        engine: Engine,
        ns_mirror: NSMirrorService,
        inventory_system: InventorySystem,
        production_system: ProductionSystem,
    ) -> TaskBoardSystem:
        """Provide task board management system."""
        return TaskBoardSystem(
            config,
            engine,
            session,
            ns_mirror=ns_mirror,
            inventory_system=inventory_system,
            production_system=production_system,
        )

    @provide(scope=Scope.REQUEST)
    def get_chat_system(self, config: Config, session: Session, sdk: SDK) -> ChatSystem:
        """Provide workshop chat system."""
        return ChatSystem(config, session, sdk)

    @provide(scope=Scope.REQUEST)
    def get_incident_system(
        self, config: Config, session: Session, chat_system: ChatSystem
    ) -> IncidentSystem:
        """Provide workshop incident tracking system."""
        return IncidentSystem(config, session, chat_system)

    @provide(scope=Scope.APP)
    def get_report_registry(self) -> ReportRegistry:
        """Provide global report block registry."""
        return ReportRegistry()

    @provide(scope=Scope.REQUEST)
    def get_report_system(
        self, config: Config, session: Session, registry: ReportRegistry
    ) -> ReportSystem:
        """Provide workshop reporting and analytics system."""
        return ReportSystem(config, session, registry)
