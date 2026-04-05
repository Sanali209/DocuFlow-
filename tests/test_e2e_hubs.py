import pytest

from docuflow.infrastructure.config import Config


@pytest.mark.anyio
async def test_multiple_sdk_instances_isolation(tmp_path):
    """TDD: Verify that multiple SDK instances can exist in isolation."""
    # Setup shared network root
    shared_root = tmp_path / "shared"
    shared_root.mkdir()

    # Node A config
    config_a = Config(
        node_id="NODE_A",
        shared_path=str(shared_root),
        database_url=f"sqlite:///{tmp_path}/node_a.db",
    )

    # Node B config
    config_b = Config(
        node_id="NODE_B",
        shared_path=str(shared_root),
        database_url=f"sqlite:///{tmp_path}/node_b.db",
    )

    # Use planned helper 'create_test_sdk'
    from tests.helpers import create_test_sdk

    sdk_a = await create_test_sdk(config_a)
    sdk_b = await create_test_sdk(config_b)

    assert sdk_a.config.node_id == "NODE_A"
    assert sdk_b.config.node_id == "NODE_B"
    assert sdk_a.config.database_url != sdk_b.config.database_url

    await sdk_a.on_shutdown()
    await sdk_b.on_shutdown()
