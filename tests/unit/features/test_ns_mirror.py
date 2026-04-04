import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool

from docuflow.features.folder_scanner.mirror import NSMirrorService
from docuflow.features.folder_scanner.settings import FolderScannerSettings
from docuflow.domain.entities.production import (
    WorkerBucketEntry, TaskItem, WorkItem, WorkLog, WorkLogType, WorkItemType
)
from docuflow.infrastructure.config import Config

@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def mock_sdk():
    sdk = MagicMock()
    
    # Mock settings resolution
    settings = FolderScannerSettings(
        sidra_scan_path="test_sidra",
        local_ns_path="test_ns",
        ns_mirror_interval_seconds=1,
        ns_mirror_copy_timeout_s=5
    )
    
    # Mock NotificationService
    notification_service = AsyncMock()
    notification_service.emit = AsyncMock()
    
    async def resolve_mock(cls):
        # Use class name comparison to avoid identity mismatches across different import paths
        name = cls.__name__ if hasattr(cls, "__name__") else str(cls)
        if "FolderScannerSettings" in name:
            return settings
        if "NotificationService" in name:
            return notification_service
        return MagicMock()

    sdk.resolve_system_by_type = AsyncMock(side_effect=resolve_mock)
    return sdk

@pytest.fixture
def service(mock_sdk, session: Session):
    config = Config(shared_path="./test_shared", node_id="test_node")
    system = NSMirrorService(config, sdk=mock_sdk, engine=session.bind)
    return system

@pytest.mark.asyncio
async def test_mirror_preserves_structure(tmp_path, service, mock_sdk, session: Session):
    """Test that GNC is copied into a subfolder matching its network path."""
    # 1. Setup mock network and local folders
    net_root = tmp_path / "network"
    ns_root = tmp_path / "local_ns"
    net_root.mkdir(); ns_root.mkdir()
    
    folder_name = "SIDRA-001"
    subfolder = net_root / folder_name
    subfolder.mkdir()
    gnc_file = subfolder / "test.GNC"
    gnc_file.write_text("CNC DATA")
    
    # 2. Update settings
    settings = await mock_sdk.resolve_system_by_type(FolderScannerSettings)
    settings.sidra_scan_path = str(net_root)
    settings.local_ns_path = str(ns_root)
    
    # 3. Setup database entries
    wi = WorkItem(
        folder_name=folder_name, 
        folder_path=folder_name, 
        work_item_type=WorkItemType.SIDRA,
        project_id=1
    )
    session.add(wi)
    session.commit(); session.refresh(wi)
    
    task = TaskItem(
        work_item_id=wi.id,
        file_name="test.GNC",
        file_path=str(gnc_file.relative_to(net_root)), # Folder1/test.GNC
        file_hash="mock_hash"
    )
    session.add(task)
    session.commit(); session.refresh(task)
    
    bucket_entry = WorkerBucketEntry(
        node_id="test_node",
        task_item_id=task.id
    )
    session.add(bucket_entry)
    session.commit()
    
    # 4. Run sync
    await service._sync_bucket(settings)
    
    # 5. Verify local file exists with correct structure
    expected_local = ns_root / folder_name / "test.GNC"
    assert expected_local.exists()
    assert expected_local.read_text() == "CNC DATA"

@pytest.mark.asyncio
async def test_mirror_logs_mismatch(tmp_path, service, mock_sdk, session: Session):
    """Test that hash mismatch generates a WorkLog event."""
    net_root = tmp_path / "network"
    ns_root = tmp_path / "local_ns"
    net_root.mkdir(); ns_root.mkdir()
    
    gnc_net = net_root / "test.GNC"
    gnc_ns  = ns_root / "test.GNC"
    gnc_net.write_text("NEW CONTENT")
    gnc_ns.write_text("OLD CONTENT")
    
    settings = await mock_sdk.resolve_system_by_type(FolderScannerSettings)
    settings.sidra_scan_path = str(net_root)
    settings.local_ns_path = str(ns_root)
    
    # 3. Setup database entries
    wi = WorkItem(folder_name="F", folder_path="", work_item_type=WorkItemType.SIDRA, project_id=1)
    session.add(wi); session.commit(); session.refresh(wi)
    
    task = TaskItem(
        work_item_id=wi.id,
        file_name="test.GNC",
        file_path="test.GNC",
        file_hash="NEW_HASH_MD5" # This hash is from network
    )
    session.add(task); session.commit(); session.refresh(task)
    
    entry = WorkerBucketEntry(node_id="test_node", task_item_id=task.id)
    session.add(entry); session.commit()
        
    # Run sync
    await service._sync_bucket(settings)
    
    # Verify log entry
    log = session.exec(select(WorkLog).where(WorkLog.log_type == WorkLogType.FILE_CHANGED)).first()
    assert log is not None
    assert "устарела" in log.message
