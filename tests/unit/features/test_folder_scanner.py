from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, select

from docuflow.domain.entities.production import (
    WorkItem,
    WorkItemStatus,
    WorkItemType,
)
from docuflow.features.folder_scanner.settings import FolderScannerSettings
from docuflow.features.folder_scanner.system import FolderScannerSystem
from docuflow.features.inventory.system import InventorySystem
from docuflow.features.notifications.system import NotificationService
from docuflow.features.parts.system import PartLibrarySystem
from docuflow.features.projects.system import ProjectSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def mock_sdk(engine):
    sdk = MagicMock()
    sdk.orchestrator = MagicMock()
    sdk.orchestrator.is_master.return_value = True

    config = Config(shared_path="./test_shared", node_id="test_node")

    # Create session properly managed by fixture
    session = Session(engine)

    # Mock settings resolution
    settings = FolderScannerSettings(
        sidra_scan_path="test_sidra", enabled=True, poll_interval_seconds=1
    )

    # Mock NotificationService
    notification_service = AsyncMock()
    notification_service.emit = AsyncMock()

    async def resolve_mock(cls):
        if cls == FolderScannerSettings:
            return settings
        if cls == NotificationService:
            return notification_service
        if cls == ProjectSystem:
            # Atomic session usage inside the mock system resolution
            with Session(engine) as session:
                return ProjectSystem(config, db_session=session)
        if cls == PartLibrarySystem:
            with Session(engine) as session:
                return PartLibrarySystem(config, db_session=session, sdk=sdk)
        if cls == InventorySystem:
            # Atomic session usage inside the mock system resolution
            with Session(engine) as session:
                return InventorySystem(config, db_session=session, sdk=sdk)
        return sdk.orchestrator

    sdk.resolve_system_by_type = resolve_mock

    yield sdk

    # Properly close session after tests
    session.close()

    sdk.resolve_system_by_type = AsyncMock(side_effect=resolve_mock)
    return sdk


@pytest.fixture
def engine(tmp_path):
    """
    Creates an in-memory SQLite engine using StaticPool for async testing.
    StaticPool ensures that all connections share the same memory space,
    making it 100% stable for async ingestion tests where multiple writers
    (systems under test) access the DB concurrently.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def scanner(mock_sdk, engine):
    """
    Standardized scanner fixture using Engine injection.
    Reflects the production architecture where the System manages its own sessions.
    """
    config = Config(shared_path="./test_shared", node_id="test_node")

    # Initialize default project using a temporary session
    from docuflow.features.projects.system import ProjectSystem

    with Session(engine) as session:
        project_system = ProjectSystem(config, db_session=session)
        project_system.resolve_default_workshop_project()
        session.commit()

    # Bridge the engine to the scanner system
    system = FolderScannerSystem(config, mock_sdk, engine=engine)
    return system


@pytest.mark.asyncio
async def test_scan_creates_work_item(tmp_path, scanner, mock_sdk, engine):
    """Test that scanning a valid folder creates a WorkItem in the DB."""
    # Setup test directory
    sidra_root = tmp_path / "sidra"
    sidra_root.mkdir()

    folder_name = "SIDRA-353203-SHLAV-2-07.07.2025"
    wi_folder = sidra_root / folder_name
    wi_folder.mkdir()

    # Create a dummy GNC file
    gnc_file = wi_folder / "01-01-SIDRA-TEST.GNC"
    gnc_file.write_text("(*SHEET 2000 1000 2 1)\n(PART NAME:TEST-PART)\n")

    settings = await mock_sdk.resolve_system_by_type(FolderScannerSettings)
    settings.sidra_scan_path = str(sidra_root)

    # Run one scan
    await scanner.scan_directory_path(sidra_root, WorkItemType.SIDRA, settings)

    # Verify DB using an atomic verification session.
    # CRITICAL: Assertions must happen INSIDE the session block to
    # prevent lazy-loading relationship access from triggering thread errors.
    with Session(engine) as session:
        wi = session.exec(select(WorkItem).where(WorkItem.folder_name == folder_name)).first()
        assert wi is not None
        assert wi.work_item_type == WorkItemType.SIDRA
        assert wi.sidra_number == "353203"
        assert wi.status == WorkItemStatus.NEW

        # Check Project creation
        from docuflow.domain.entities.production import Project

        project = session.exec(select(Project).where(Project.id == wi.project_id)).first()
        assert project is not None
        assert project.name == "Default"


@pytest.mark.asyncio
async def test_scan_pending_cuts_on_empty_folder(tmp_path, scanner, mock_sdk, engine):
    """Test that a folder with no GNC files gets PENDING_CUTS status."""
    sidra_root = tmp_path / "sidra"
    sidra_root.mkdir()

    wi_folder = sidra_root / "SIDRA-123456-STEP-01.01.2025"
    wi_folder.mkdir()

    settings = await mock_sdk.resolve_system_by_type(FolderScannerSettings)
    await scanner.scan_directory_path(sidra_root, WorkItemType.SIDRA, settings)

    with Session(engine) as session:
        wi = session.exec(select(WorkItem)).first()
        assert wi.status == WorkItemStatus.PENDING_CUTS


@pytest.mark.asyncio
async def test_always_start_loop_on_startup(mock_sdk, scanner):
    """Test that polling loop always starts for symmetric logic, regardless of Master status."""
    mock_sdk.orchestrator.is_master.return_value = False

    # We use a mock that returns a completed future to avoid 'never awaited' warnings
    with patch("asyncio.create_task") as mock_create_task:
        mock_task = MagicMock()
        mock_create_task.return_value = mock_task

        await scanner.on_startup()
        mock_create_task.assert_called_once()
        assert scanner._is_active_polling is True

    # Cleanup
    scanner._is_active_polling = False
