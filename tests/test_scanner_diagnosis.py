"""
Diagnostic tests for FolderScannerSystem.

These tests help diagnose why the scanner is not working:
- SIDRA PATH shows OK
- Enabled = True OK
- Last scan: Never PROBLEM
- SCAN NOW button triggers 2 notifications but nothing happens PROBLEM

TDD Approach: RED → GREEN → REFACTOR
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from docuflow.features.folder_scanner.settings import FolderScannerSettings
from docuflow.features.folder_scanner.system import FolderScannerSystem
from docuflow.infrastructure.config import Config


class TestScannerDiagnosis:
    """Diagnostic tests to identify scanner issues."""

    @pytest.fixture
    def real_db_engine(self, tmp_path):
        """Create a real SQLite engine with all tables."""

        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock config."""
        config = MagicMock(spec=Config)
        config.node_id = "node_01"
        config.shared_path = str(tmp_path)
        return config

    @pytest.fixture
    def mock_sdk_master(self):
        """Create a mock SDK that returns True for is_master()."""
        from contextlib import asynccontextmanager

        sdk = MagicMock()
        sdk.orchestrator.is_leader = True

        @asynccontextmanager
        async def mock_scope():
            yield MagicMock()

        sdk.request_scope = mock_scope

        async def resolve_mock(stype):
            mock_sys = MagicMock()
            mock_sys.emit = AsyncMock()  # For NotificationService
            if "ProjectSystem" in str(stype):
                proj = MagicMock()
                proj.id = 1
                mock_sys.resolve_default_workshop_project.return_value = proj
            return mock_sys

        sdk.resolve_system_by_type = resolve_mock
        return sdk

    @pytest.fixture
    def mock_sdk_slave(self):
        """Create a mock SDK that returns False for is_master()."""
        from contextlib import asynccontextmanager

        sdk = MagicMock()
        sdk.orchestrator.is_leader = False

        @asynccontextmanager
        async def mock_scope():
            yield MagicMock()

        sdk.request_scope = mock_scope

        async def resolve_mock(stype):
            return MagicMock()

        sdk.resolve_system_by_type = resolve_mock
        return sdk

    @pytest.fixture
    def mock_sdk_no_orchestrator(self):
        """Create a mock SDK with no orchestrator."""
        from contextlib import asynccontextmanager

        sdk = MagicMock()
        # Simulate orchestrator missing
        del sdk.orchestrator

        @asynccontextmanager
        async def mock_scope():
            yield MagicMock()

        sdk.request_scope = mock_scope
        return sdk

    @pytest.fixture
    def admin_with_settings(self, real_db_engine):
        """Create admin system with proper settings."""
        from docuflow.domain.entities.identity import NodeSetting
        from docuflow.features.admin.system import AdminSystem

        config = MagicMock(spec=Config)
        config.node_id = "node_01"
        config.shared_path = "/tmp"

        orchestrator = MagicMock()
        signer = MagicMock()

        admin = AdminSystem(
            engine=real_db_engine, orchestrator=orchestrator, signer=signer, config=config
        )

        # Add settings to database
        with Session(real_db_engine) as session:
            settings = [
                NodeSetting(
                    node_id="node_01",
                    module="folder_scanner",
                    key="sidra_scan_path",
                    value="D:\\github\\DocuFlow-\\data_sample\\sidra",
                ),
                NodeSetting(
                    node_id="node_01", module="folder_scanner", key="enabled", value="True"
                ),
            ]
            for s in settings:
                session.add(s)
            session.commit()

        return admin

    @pytest.fixture
    def admin_without_settings(self, real_db_engine):
        """Create admin system without settings (to test defaults)."""
        from docuflow.features.admin.system import AdminSystem

        config = MagicMock(spec=Config)
        config.node_id = "node_01"
        config.shared_path = "/tmp"

        orchestrator = MagicMock()
        signer = MagicMock()

        admin = AdminSystem(
            engine=real_db_engine, orchestrator=orchestrator, signer=signer, config=config
        )

        return admin

    # ==========================================
    # DIAGNOSTIC TEST 1: _is_master() behavior
    # ==========================================

    @pytest.mark.asyncio
    async def test_diagnosis_is_master_returns_true_on_master(
        self, mock_config, mock_sdk_master, real_db_engine, admin_with_settings
    ):
        """
        DIAGNOSIS: Verify _is_master() returns True when SDK says we are master.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_master,
            engine=real_db_engine,
            admin_system=admin_with_settings,
        )

        result = scanner._is_master

        assert result is True, "Expected _is_master() to return True on master node"

    @pytest.mark.asyncio
    async def test_diagnosis_is_master_returns_false_on_slave(
        self, mock_config, mock_sdk_slave, real_db_engine, admin_with_settings
    ):
        """
        DIAGNOSIS: Verify _is_master() returns False when SDK says we are slave.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_slave,
            engine=real_db_engine,
            admin_system=admin_with_settings,
        )

        result = scanner._is_master

        assert result is False, "Expected _is_master() to return False on slave node"

    @pytest.mark.asyncio
    async def test_diagnosis_is_master_returns_false_when_orchestrator_none(
        self, mock_config, mock_sdk_no_orchestrator, real_db_engine, admin_with_settings
    ):
        """
        DIAGNOSIS: Verify _is_master() returns False when orchestrator is not initialized.
        This is a common issue - if SDK.on_startup() wasn't called properly.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_no_orchestrator,
            engine=real_db_engine,
            admin_system=admin_with_settings,
        )

        result = await scanner._is_master()

        assert result is False, "Expected _is_master() to return False when orchestrator is None"

    # ==========================================
    # DIAGNOSTIC TEST 2: Settings reading
    # ==========================================

    def test_diagnosis_settings_read_from_db(
        self, mock_config, mock_sdk_master, real_db_engine, admin_with_settings
    ):
        """
        DIAGNOSIS: Verify settings are correctly read from database.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_master,
            engine=real_db_engine,
            admin_system=admin_with_settings,
        )

        settings = scanner.get_settings("node_01")

        assert settings.sidra_scan_path == "D:\\github\\DocuFlow-\\data_sample\\sidra", (
            f"Expected sidra_scan_path to be set, got: {settings.sidra_scan_path}"
        )
        assert settings.enabled is True, f"Expected enabled to be True, got: {settings.enabled}"

    def test_diagnosis_settings_defaults_when_no_admin(
        self, mock_config, mock_sdk_master, real_db_engine
    ):
        """
        DIAGNOSIS: Verify default settings when admin_system is None.
        This simulates the issue where settings are not configured.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_master,
            engine=real_db_engine,
            admin_system=None,  # No admin system!
        )

        settings = scanner.get_settings("node_01")

        # Default values
        assert settings.sidra_scan_path == "", (
            f"Expected default sidra_scan_path to be empty, got: {settings.sidra_scan_path}"
        )
        assert settings.enabled is True, (
            f"Expected default enabled to be True, got: {settings.enabled}"
        )

    def test_diagnosis_settings_defaults_when_not_in_db(
        self, mock_config, mock_sdk_master, real_db_engine, admin_without_settings
    ):
        """
        DIAGNOSIS: Verify default settings when settings are not in database.
        This is the most likely cause of the issue!
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_master,
            engine=real_db_engine,
            admin_system=admin_without_settings,
        )

        settings = scanner.get_settings("node_01")

        # Default values - THIS IS THE PROBLEM!
        assert settings.sidra_scan_path == "", (
            f"Expected default sidra_scan_path to be empty, got: {settings.sidra_scan_path}"
        )
        # If we get here, the problem is confirmed:
        # sidra_scan_path is empty by default, so _scan_all() will skip SIDRA scanning!

    # ==========================================
    # DIAGNOSTIC TEST 3: scan_now() behavior
    # ==========================================

    @pytest.mark.asyncio
    async def test_diagnosis_scan_now_completes_on_master(
        self, mock_config, mock_sdk_master, real_db_engine, admin_with_settings, tmp_path
    ):
        """
        DIAGNOSIS: Verify scan_now() completes successfully on master with proper settings.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_master,
            engine=real_db_engine,
            admin_system=admin_with_settings,
        )

        # Create a test folder structure
        test_sidra_dir = tmp_path / "sidra"
        test_sidra_dir.mkdir()
        test_folder = test_sidra_dir / "SIDRA-123456-SHLAV-1-01.01.2025"
        test_folder.mkdir()

        # Update settings to use test path
        with Session(real_db_engine) as session:
            from docuflow.domain.entities.identity import NodeSetting

            setting = session.exec(
                select(NodeSetting).where(
                    NodeSetting.node_id == "node_01",
                    NodeSetting.module == "folder_scanner",
                    NodeSetting.key == "sidra_scan_path",
                )
            ).first()
            setting.value = str(test_sidra_dir)
            session.commit()

        # Execute
        await scanner.scan_now()

        # Verify
        assert scanner._last_scan_time is not None, (
            "Expected _last_scan_time to be set after scan_now()"
        )

    @pytest.mark.asyncio
    async def test_diagnosis_scan_now_skipped_on_slave(
        self, mock_config, mock_sdk_slave, real_db_engine, admin_with_settings
    ):
        """
        DIAGNOSIS: Verify scan_now() is skipped on slave node.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_slave,
            engine=real_db_engine,
            admin_system=admin_with_settings,
        )

        # Execute
        await scanner.scan_now()

        # Verify
        assert scanner._last_scan_time is None, (
            "Expected _last_scan_time to remain None on slave node"
        )

    @pytest.mark.asyncio
    async def test_diagnosis_scan_now_skipped_when_disabled(
        self, mock_config, mock_sdk_master, real_db_engine, admin_with_settings
    ):
        """
        DIAGNOSIS: Verify scan_now() is skipped when scanner is disabled.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_master,
            engine=real_db_engine,
            admin_system=admin_with_settings,
        )

        # Disable scanner
        with Session(real_db_engine) as session:
            from docuflow.domain.entities.identity import NodeSetting

            setting = session.exec(
                select(NodeSetting).where(
                    NodeSetting.node_id == "node_01",
                    NodeSetting.module == "folder_scanner",
                    NodeSetting.key == "enabled",
                )
            ).first()
            setting.value = "False"
            session.commit()

        # Execute
        await scanner.scan_now()

        # Verify
        assert scanner._last_scan_time is None, (
            "Expected _last_scan_time to remain None when disabled"
        )

    # ==========================================
    # DIAGNOSTIC TEST 4: _scan_all() behavior
    # ==========================================

    @pytest.mark.asyncio
    async def test_diagnosis_scan_all_skips_empty_path(
        self, mock_config, mock_sdk_master, real_db_engine, admin_without_settings
    ):
        """
        DIAGNOSIS: Verify _scan_all() skips empty paths.
        This is the ROOT CAUSE of "Last scan: Never" issue!
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_master,
            engine=real_db_engine,
            admin_system=admin_without_settings,
        )

        settings = FolderScannerSettings(
            sidra_scan_path="",  # Empty path!
            enabled=True,
        )

        # Execute
        await scanner._scan_all(settings)

        # Verify - _last_scan_time is set even if path is empty
        assert scanner._last_scan_time is not None, (
            "Expected _last_scan_time to be set even with empty path"
        )
        # But no folders were scanned because path was empty!

    @pytest.mark.asyncio
    async def test_diagnosis_scan_all_processes_existing_path(
        self, mock_config, mock_sdk_master, real_db_engine, tmp_path
    ):
        """
        DIAGNOSIS: Verify _scan_all() processes existing paths.
        """
        scanner = FolderScannerSystem(
            config=mock_config, sdk=mock_sdk_master, engine=real_db_engine, admin_system=None
        )

        # Create test folder
        test_dir = tmp_path / "sidra"
        test_dir.mkdir()

        settings = FolderScannerSettings(sidra_scan_path=str(test_dir), enabled=True)

        # Execute
        await scanner._scan_all(settings)

        # Verify
        assert scanner._last_scan_time is not None, (
            "Expected _last_scan_time to be set after scanning"
        )

    # ==========================================
    # DIAGNOSTIC TEST 5: Full integration test
    # ==========================================

    @pytest.mark.asyncio
    async def test_diagnosis_full_scan_workflow(
        self, mock_config, mock_sdk_master, real_db_engine, tmp_path
    ):
        """
        DIAGNOSIS: Full integration test simulating the actual workflow.
        This test reproduces the exact issue reported by the user.
        """
        # Setup: Create admin with proper settings
        from docuflow.features.admin.system import AdminSystem

        config = MagicMock(spec=Config)
        config.node_id = "node_01"
        config.shared_path = str(tmp_path)

        orchestrator = MagicMock()
        signer = MagicMock()

        admin = AdminSystem(
            engine=real_db_engine, orchestrator=orchestrator, signer=signer, config=config
        )

        # Add settings to database
        with Session(real_db_engine) as session:
            from docuflow.domain.entities.identity import NodeSetting

            settings = [
                NodeSetting(
                    node_id="node_01",
                    module="folder_scanner",
                    key="sidra_scan_path",
                    value=str(tmp_path / "sidra"),
                ),
                NodeSetting(
                    node_id="node_01", module="folder_scanner", key="enabled", value="True"
                ),
            ]
            for s in settings:
                session.add(s)
            session.commit()

        # Create test folder structure
        sidra_dir = tmp_path / "sidra"
        sidra_dir.mkdir()
        test_folder = sidra_dir / "SIDRA-353203-SHLAV-2-07.07.2025"
        test_folder.mkdir()

        # Create scanner
        scanner = FolderScannerSystem(
            config=mock_config, sdk=mock_sdk_master, engine=real_db_engine, admin_system=admin
        )

        # Verify initial state
        status = scanner.get_status()
        assert status["last_scan_time"] is None, "Initial last_scan_time should be None"
        assert status["is_running"] is False, "Initial is_running should be False"

        # Execute scan_now()
        await scanner.scan_now()

        # Verify final state
        status = scanner.get_status()
        assert status["last_scan_time"] is not None, "last_scan_time should be set after scan_now()"

    # ==========================================
    # TDD TEST 6: Bug #1 - admin_system injection
    # ==========================================

    def test_bug1_admin_system_must_be_injected(
        self, mock_config, mock_sdk_master, real_db_engine, admin_with_settings
    ):
        """
        RED: admin_system должен быть передан через DI, а не через workaround.
        """
        scanner = FolderScannerSystem(
            config=mock_config,
            sdk=mock_sdk_master,
            engine=real_db_engine,
            admin_system=admin_with_settings,
        )

        # Verify admin_system is set
        assert scanner._admin is not None, "admin_system must be injected, not None"

        # Verify settings are read from DB, not defaults
        settings = scanner.get_settings("node_01")
        assert settings.sidra_scan_path != "", (
            "sidra_scan_path should not be empty when admin_system is injected"
        )

    # ==========================================
    # TDD TEST 7: Bug #2 - WorkLog creation
    # ==========================================

    @pytest.mark.asyncio
    async def test_bug2_scan_must_create_worklog(
        self, mock_config, mock_sdk_master, real_db_engine, tmp_path
    ):
        """
        RED: Сканирование должно создавать WorkLog записи.
        Currently WorkLog is only created in _process_gnc() on file change.
        """
        from docuflow.domain.entities.production import WorkLog
        from docuflow.features.admin.system import AdminSystem

        config = MagicMock(spec=Config)
        config.node_id = "node_01"
        config.shared_path = str(tmp_path)

        orchestrator = MagicMock()
        signer = MagicMock()

        admin = AdminSystem(
            engine=real_db_engine, orchestrator=orchestrator, signer=signer, config=config
        )

        # Setup settings
        with Session(real_db_engine) as session:
            from docuflow.domain.entities.identity import NodeSetting

            settings = [
                NodeSetting(
                    node_id="node_01",
                    module="folder_scanner",
                    key="sidra_scan_path",
                    value=str(tmp_path / "sidra"),
                ),
                NodeSetting(
                    node_id="node_01", module="folder_scanner", key="enabled", value="True"
                ),
            ]
            for s in settings:
                session.add(s)
            session.commit()

        # Create test folder
        sidra_dir = tmp_path / "sidra"
        sidra_dir.mkdir()
        test_folder = sidra_dir / "SIDRA-123456-SHLAV-1-01.01.2025"
        test_folder.mkdir()

        scanner = FolderScannerSystem(
            config=mock_config, sdk=mock_sdk_master, engine=real_db_engine, admin_system=admin
        )

        # Verify initial state: no WorkLogs
        with Session(real_db_engine) as session:
            initial_logs = session.exec(select(WorkLog)).all()
            assert len(initial_logs) == 0, "Should start with no WorkLogs"

        # Execute scan
        await scanner.scan_now()

        # Verify: WorkLog should be created
        with Session(real_db_engine) as session:
            logs = session.exec(select(WorkLog)).all()
            assert len(logs) > 0, "Scan should create at least one WorkLog entry"

            # Verify log message mentions scanning
            scan_logs = [l for l in logs if "scan" in l.message.lower()]
            assert len(scan_logs) > 0, "WorkLog should contain scan-related messages"

    # ==========================================
    # TDD TEST 8: Bug #4 - _files_found reset
    # ==========================================

    @pytest.mark.asyncio
    async def test_bug4_files_found_must_reset_on_scan(
        self, mock_config, mock_sdk_master, real_db_engine, tmp_path
    ):
        """
        RED: _files_found должен сбрасываться при каждом сканировании.
        Currently it only increments and never resets.
        """
        from docuflow.features.admin.system import AdminSystem

        # Create an empty directory for scanning (no subfolders)
        empty_dir = tmp_path / "empty_scan_dir"
        empty_dir.mkdir()

        config = MagicMock(spec=Config)
        config.node_id = "node_01"
        config.shared_path = str(tmp_path)

        orchestrator = MagicMock()
        signer = MagicMock()

        admin = AdminSystem(
            engine=real_db_engine, orchestrator=orchestrator, signer=signer, config=config
        )

        scanner = FolderScannerSystem(
            config=mock_config, sdk=mock_sdk_master, engine=real_db_engine, admin_system=admin
        )

        # Simulate previous scan with files
        scanner._files_found = 100

        # Execute new scan (empty folder)
        await scanner._scan_all(FolderScannerSettings(sidra_scan_path=str(empty_dir), enabled=True))

        # Verify: _files_found should be 0 (reset), not 100
        assert scanner._files_found == 0, (
            f"_files_found should reset to 0 at start of each scan, but got {scanner._files_found}"
        )
