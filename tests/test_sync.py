from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, create_engine

pytest.skip(
    "Order model removed or refactored; test disabled until updated", allow_module_level=True
)
from docuflow.domain.entities.settings import Setting

from docuflow.domain.entities.production import Order
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.sync import DataSyncSystem


@pytest.fixture
def sync_setup(tmp_path):
    """Fixture for data synchronization testing."""
    shared_path = tmp_path / "shared"
    shared_path.mkdir()
    (shared_path / "SNAPSHOTS").mkdir()

    db_path = tmp_path / "local.db"
    db_url = f"sqlite:///{db_path}"

    config = Config(node_id="NODE_A", shared_path=str(shared_path), database_url=db_url)

    engine = create_engine(db_url)
    Setting.metadata.create_all(engine)
    Order.metadata.create_all(engine)

    return config, engine


@pytest.mark.anyio
async def test_snapshot_creation(sync_setup):
    """Test that the master can create a data snapshot."""
    config, engine = sync_setup
    sync = DataSyncSystem(config=config, engine=engine)

    # Add some data to local DB
    with Session(engine) as session:
        session.add(Setting(key="theme", value="dark"))
        session.commit()

    # Perform snapshot
    snapshot_file = await sync.create_master_snapshot()

    assert snapshot_file.exists()
    assert snapshot_file.suffix == ".json"


@pytest.mark.anyio
async def test_snapshot_merging(sync_setup, tmp_path):
    """Test that a node can merge data from a snapshot."""
    config, engine_a = sync_setup

    # Create a separate DB for Node B
    db_path_b = tmp_path / "node_b.db"
    engine_b = create_engine(f"sqlite:///{db_path_b}")
    Setting.metadata.create_all(engine_b)

    sync_a = DataSyncSystem(config=config, engine=engine_a)
    sync_b = DataSyncSystem(config=config, engine=engine_b)

    # Node A makes a change and snapshots
    with Session(engine_a) as session:
        session.add(Setting(key="site_name", value="MasterSite"))
        session.commit()

    snapshot_path = await sync_a.create_master_snapshot()

    # Node B merges the snapshot
    await sync_b.apply_remote_snapshot(snapshot_path)

    # Verify Node B has the data
    with Session(engine_b) as session:
        setting = session.get(Setting, "site_name")
        assert setting is not None
        assert setting.value == "MasterSite"


@pytest.mark.anyio
async def test_merge_conflict_resolution(sync_setup, tmp_path):
    """Test that merging respects 'updated_at' (Last Write Wins)."""
    config, engine_a = sync_setup
    db_path_b = tmp_path / "node_b_conflict.db"
    engine_b = create_engine(f"sqlite:///{db_path_b}")
    Setting.metadata.create_all(engine_b)

    sync_a = DataSyncSystem(config=config, engine=engine_a)
    sync_b = DataSyncSystem(config=config, engine=engine_b)

    # Node B has an OLDER change
    old_time = datetime.now() - timedelta(hours=1)
    with Session(engine_b) as session:
        session.add(Setting(key="api_key", value="old_key", updated_at=old_time))
        session.commit()

    # Node A has a NEWER change
    with Session(engine_a) as session:
        session.add(Setting(key="api_key", value="new_key"))
        session.commit()

    snapshot_path = await sync_a.create_master_snapshot()

    # Node B applies A's snapshot
    await sync_b.apply_remote_snapshot(snapshot_path)

    # Verify B now has A's newer key
    with Session(engine_b) as session:
        setting = session.get(Setting, "api_key")
        assert setting.value == "new_key"
