"""Integration tests for FolderScannerSystem."""

from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from docuflow.domain.entities.identity import NodeSetting
from docuflow.domain.entities.production import Project
from docuflow.features.folder_scanner.settings import FolderScannerSettings
from docuflow.features.folder_scanner.system import FolderScannerSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def mock_engine(tmp_path):
    """Create a real SQLite engine for testing."""
    from sqlalchemy import create_engine
    from sqlmodel import SQLModel

    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config with temporary paths."""
    config = MagicMock(spec=Config)
    config.node_id = "node_01"
    config.shared_path = str(tmp_path)
    return config


@pytest.fixture
def mock_sdk(mock_engine):
    """Create a mock SDK."""
    sdk = MagicMock()
    sdk.is_master.return_value = True

    # Add async resolve_system_by_type mock that returns proper mocks
    async def mock_resolve(system_cls):
        # Create a real default project in the test database
        from sqlmodel import Session, select

        with Session(mock_engine) as session:
            default_project = session.exec(select(Project).where(Project.name == "Default")).first()
            if not default_project:
                default_project = Project(name="Default", is_default=True)
                session.add(default_project)
                session.commit()
                session.refresh(default_project)

        # Return a mock that has the required method
        mock_system = MagicMock()
        mock_system.resolve_default_workshop_project.return_value = default_project
        return mock_system

    sdk.resolve_system_by_type = AsyncMock(side_effect=mock_resolve)

    @asynccontextmanager
    async def mock_request_scope():
        yield sdk

    sdk.request_scope = mock_request_scope
    return sdk


@pytest.fixture
def mock_admin_system(mock_engine):
    """Create a mock admin system with real engine."""
    from sqlmodel import Session

    from docuflow.application.bus.orchestrator import P2POrchestrator
    from docuflow.features.admin.system import AdminSystem
    from docuflow.infrastructure.config import Config
    from docuflow.infrastructure.security import HMACSigner

    config = MagicMock(spec=Config)
    config.node_id = "node_01"
    config.shared_path = "/tmp"

    orchestrator = MagicMock(spec=P2POrchestrator)
    signer = MagicMock(spec=HMACSigner)

    admin = AdminSystem(engine=mock_engine, orchestrator=orchestrator, signer=signer, config=config)

    # Seed test data
    with Session(mock_engine) as session:
        setting = NodeSetting(
            node_id="node_01",
            module="folder_scanner",
            key="sidra_scan_path",
            value="D:\\github\\DocuFlow-\\assets\\fixtures\\data_sample\\sidra",
        )
        session.add(setting)

        setting2 = NodeSetting(
            node_id="node_01", module="folder_scanner", key="enabled", value="True"
        )
        session.add(setting2)
        session.commit()

    return admin


@pytest.fixture
def scanner_system(mock_config, mock_sdk, mock_engine, mock_admin_system):
    """Create FolderScannerSystem with mocks."""
    return FolderScannerSystem(
        config=mock_config, sdk=mock_sdk, engine=mock_engine, admin_system=mock_admin_system
    )


@pytest.mark.asyncio
async def test_scan_now_on_master(scanner_system):
    """Test that scan_now() works on master node."""
    # Setup
    scanner_system.sdk.is_master.return_value = True

    # Execute
    await scanner_system.scan_now()

    # Verify
    scanner_system.sdk.is_master.assert_called_once()
    assert scanner_system._last_scan_time is not None


@pytest.mark.asyncio
async def test_scan_now_on_slave(scanner_system):
    """Test that scan_now() is ignored on slave node."""
    # Setup
    scanner_system.sdk.is_master.return_value = False

    # Execute
    await scanner_system.scan_now()

    # Verify
    scanner_system.sdk.is_master.assert_called_once()
    assert scanner_system._last_scan_time is None


@pytest.mark.asyncio
async def test_scan_now_disabled(scanner_system):
    """Test that scan_now() is ignored when disabled."""
    # Setup
    scanner_system.sdk.is_master.return_value = True

    # Mock admin_system.get_node_settings to return disabled settings
    original_get_node_settings = scanner_system._admin.get_node_settings
    scanner_system._admin.get_node_settings = MagicMock(
        return_value={"enabled": False, "sidra_scan_path": "/some/path"}
    )

    # Execute
    await scanner_system.scan_now()

    # Verify
    assert scanner_system._last_scan_time is None

    # Restore
    scanner_system._admin.get_node_settings = original_get_node_settings


def test_get_settings_from_db(scanner_system):
    """Test that get_settings() reads from database."""
    # Mock admin_system.get_node_settings
    original_get_node_settings = scanner_system._admin.get_node_settings
    mock_get = MagicMock(
        return_value={
            "sidra_scan_path": "D:\\github\\DocuFlow-\\assets\\fixtures\\data_sample\\sidra",
            "enabled": True,
        }
    )
    scanner_system._admin.get_node_settings = mock_get

    # Execute
    settings = scanner_system.get_settings("node_01")

    # Verify
    mock_get.assert_called_once_with("node_01", "folder_scanner")
    assert settings.sidra_scan_path == "D:\\github\\DocuFlow-\\assets\\fixtures\\data_sample\\sidra"
    assert settings.enabled is True

    # Restore
    scanner_system._admin.get_node_settings = original_get_node_settings


def test_get_settings_without_admin(mock_config, mock_sdk, mock_engine):
    """Test that get_settings() returns defaults without admin_system."""
    # Setup
    scanner = FolderScannerSystem(
        config=mock_config, sdk=mock_sdk, engine=mock_engine, admin_system=None
    )

    # Execute
    settings = scanner.get_settings("node_01")

    # Verify
    assert settings.sidra_scan_path == ""  # Default value
    assert settings.enabled is True  # Default value


def test_get_status(scanner_system):
    """Test that get_status() returns correct data."""
    # Setup
    scanner_system._is_active_polling = True
    scanner_system._last_successful_scan = datetime(2026, 4, 3, 6, 0, 0)
    scanner_system._items_discovered_count = 42

    # Execute
    status = scanner_system.get_status()

    # Verify
    assert status["is_running"] is True
    assert status["last_scan_at"] == datetime(2026, 4, 3, 6, 0, 0)
    assert status["files_found"] == 42

    assert status["is_master"] is True


@pytest.mark.asyncio
async def test_scan_all_with_existing_path(scanner_system, tmp_path):
    """Test that _scan_all() scans existing paths."""
    # Setup
    test_dir = tmp_path / "test_folder"
    test_dir.mkdir()

    settings = FolderScannerSettings(sidra_scan_path=str(tmp_path), enabled=True)

    # Execute
    await scanner_system._scan_all(settings)

    # Verify
    assert scanner_system._last_scan_time is not None


@pytest.mark.asyncio
async def test_scan_all_with_nonexistent_path(scanner_system):
    """Test that _scan_all() handles non-existent paths."""
    # Setup
    settings = FolderScannerSettings(sidra_scan_path="/nonexistent/path", enabled=True)

    # Execute
    await scanner_system._scan_all(settings)

    # Verify - should complete without error
    assert scanner_system._last_scan_time is not None
