"""TDD Tests for CONFIGURATION tab in Admin Panel."""

from unittest.mock import AsyncMock, MagicMock

import pytest

nicegui = pytest.importorskip("nicegui")
if not hasattr(nicegui, "testing") or not hasattr(nicegui.testing, "user_simulation"):
    pytest.skip("requires nicegui.testing.user_simulation", allow_module_level=True)
from nicegui.testing import user_simulation

from docuflow.features.admin.view import admin_view


@pytest.mark.asyncio
async def test_configuration_tab_shows_module_selector():
    """RED: CONFIGURATION tab should show module selector with registered modules."""
    # 1. Setup Mock AdminSystem
    admin_system = MagicMock()
    admin_system.get_all_users.return_value = []
    admin_system.get_all_roles.return_value = []
    admin_system.get_cluster_nodes = AsyncMock(return_value=[])
    admin_system.get_node_settings.return_value = {}

    # 2. Use user_simulation to test the component
    async with user_simulation(lambda: admin_view(admin_system)) as user:
        await user.open("/")

        # 3. Click CONFIGURATION tab
        user.find("CONFIGURATION").click()

        # 4. Should see module selector label
        await user.should_see("Select Module")

        # 5. Should see scope selector
        await user.should_see("Scope")


@pytest.mark.asyncio
async def test_configuration_shows_global_settings_fields():
    """RED: When scope is Global, should show fields with scope='global'."""
    # 1. Setup Mock AdminSystem
    admin_system = MagicMock()
    admin_system.get_all_users.return_value = []
    admin_system.get_all_roles.return_value = []
    admin_system.get_cluster_nodes = AsyncMock(return_value=[])
    admin_system.get_node_settings.return_value = {}  # Empty = defaults

    # 2. Use user_simulation
    async with user_simulation(lambda: admin_view(admin_system)) as user:
        await user.open("/")

        # 3. Click CONFIGURATION tab
        user.find("CONFIGURATION").click()

        # 4. Should see Global scope selected by default
        await user.should_see("Global")

        # 5. Should see settings form title
        await user.should_see("GLOBAL SETTINGS")


@pytest.mark.asyncio
async def test_configuration_shows_local_settings_when_node_selected():
    """RED: When scope is local (node selected), should show fields with scope='local'."""
    # 1. Setup Mock AdminSystem with nodes
    admin_system = MagicMock()
    admin_system.get_all_users.return_value = []
    admin_system.get_all_roles.return_value = []
    admin_system.get_cluster_nodes = AsyncMock(
        return_value=[
            {
                "node_id": "node_01",
                "status": "ONLINE",
                "is_leader": True,
                "last_active": "2026-04-03",
            }
        ]
    )
    admin_system.get_node_settings.return_value = {}

    # 2. Use user_simulation
    async with user_simulation(lambda: admin_view(admin_system)) as user:
        await user.open("/")

        # 3. Click CONFIGURATION tab
        user.find("CONFIGURATION").click()

        # 4. Wait for nodes to load
        import asyncio

        await asyncio.sleep(1)

        # 5. Should see node in scope selector
        await user.should_see("node_01")


@pytest.mark.asyncio
async def test_configuration_settings_persist_on_change():
    """RED: When user changes a setting, should call admin_system.update_node_setting()."""
    # 1. Setup Mock AdminSystem
    admin_system = MagicMock()
    admin_system.get_all_users.return_value = []
    admin_system.get_all_roles.return_value = []
    admin_system.get_cluster_nodes = AsyncMock(return_value=[])
    admin_system.get_node_settings.return_value = {"enabled": "true"}

    # 2. Use user_simulation
    async with user_simulation(lambda: admin_view(admin_system)) as user:
        await user.open("/")

        # 3. Click CONFIGURATION tab
        user.find("CONFIGURATION").click()

        # 4. Should see settings form
        await user.should_see("GLOBAL SETTINGS")

        # 5. Verify get_node_settings was called
        admin_system.get_node_settings.assert_called()
