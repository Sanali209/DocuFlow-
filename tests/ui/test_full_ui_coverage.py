from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from nicegui.testing import user_simulation

from docuflow.features.admin.system import AdminSystem
from docuflow.features.admin.view import admin_view
from docuflow.features.analytics.view import analytics_view

# Import all views
from docuflow.features.auth.view import login_view
from docuflow.features.chat.incident_view import IncidentView
from docuflow.features.chat.view import ChatView
from docuflow.features.consumables.view import ConsumableView
from docuflow.features.dashboard.view import dashboard_view
from docuflow.features.docs.portal import DocumentationPortal
from docuflow.features.inventory.view import warehouse_view
from docuflow.features.parts.view import PartLibraryView
from docuflow.features.production.view import production_view
from docuflow.features.projects.view import ProjectManagementView
from docuflow.features.reports.view import ReportsView
from docuflow.features.task_board.view import TaskBoardView
from docuflow.features.work_items.view import WorkItemsView


@pytest.fixture
def mock_session():
    s = MagicMock()
    # Force result counts to be integers
    s.exec.return_value.one.return_value = 0
    s.exec.return_value.all.return_value = []
    # Support context manager
    s.__enter__.return_value = s
    return s


@pytest.fixture
def system_provider():
    async def provider(stype):
        return MagicMock()

    return provider


@pytest.mark.asyncio
async def test_smoke_login():
    async with user_simulation(lambda: login_view(MagicMock(), MagicMock(), "node_01")) as user:
        await user.open("/")
        await user.should_see("DocuFlow")


@pytest.mark.asyncio
async def test_smoke_dashboard(mock_session, system_provider):
    admin_sys = MagicMock()
    admin_sys.get_cluster_nodes = AsyncMock(return_value=[])
    admin_sys.session.get_bind.return_value = MagicMock()

    # Also mock the system provider to return our admin_sys when requested
    async def mock_provider(stype):
        if stype == AdminSystem:
            return admin_sys
        return MagicMock()

    layout = MagicMock()

    # Use patch to ensure any Session() call returns our mock
    with patch("docuflow.features.dashboard.view.Session", return_value=mock_session):

        async def view():
            await dashboard_view(MagicMock(), admin_sys, mock_provider, layout)

        async with user_simulation(view) as user:
            await user.open("/")
            await user.should_see("Management")


@pytest.mark.asyncio
async def test_smoke_work_items(system_provider):
    sys = MagicMock()
    sys.list_work_items_by_filter.return_value = []
    async with user_simulation(
        lambda: WorkItemsView(sys, MagicMock(), system_provider=system_provider).render()
    ) as user:
        await user.open("/")
        await user.should_see("Статус")


@pytest.mark.asyncio
async def test_smoke_task_board(mock_session, system_provider):
    sys = MagicMock()
    sys.get_bucket.return_value = []
    async with user_simulation(
        lambda: TaskBoardView(
            mock_session, sys, MagicMock(), system_provider=system_provider
        ).render()
    ) as user:
        await user.open("/")
        await user.should_see("Роль")


@pytest.mark.asyncio
async def test_smoke_warehouse(system_provider):
    sys = MagicMock()
    sys.get_material_catalog.return_value = []
    layout = MagicMock()

    async def view():
        # Patch session here too
        with patch("docuflow.features.inventory.view.select", MagicMock()):
            await warehouse_view(sys, system_provider, layout)

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("Склад")


@pytest.mark.asyncio
async def test_smoke_production():
    sys = MagicMock()
    sys.get_recent_production_units.return_value = []

    async def view():
        await production_view(sys, current_user="admin")

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("Паллетами")


@pytest.mark.asyncio
async def test_smoke_part_library():
    sys = MagicMock()
    sys.list_parts.return_value = []

    async def view():
        await PartLibraryView(sys).render()

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("деталей")


@pytest.mark.asyncio
async def test_smoke_consumables():
    sys = MagicMock()

    async def view():
        await ConsumableView(sys).render()

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("материалов")


@pytest.mark.asyncio
async def test_smoke_chat(system_provider):
    sys = MagicMock()
    sys.send_message = AsyncMock()
    layout = MagicMock()

    async def view():
        await ChatView(sys, system_provider=system_provider, layout=layout).render_portal()

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("CHANNELS")


@pytest.mark.asyncio
async def test_smoke_incidents(system_provider):
    sys = MagicMock()
    sys.get_active_incidents.return_value = []
    sys.get_recent_history.return_value = []
    layout = MagicMock()

    async def view():
        await IncidentView(sys, system_provider=system_provider, layout=layout).render_dashboard()

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("BLOCKERS")


@pytest.mark.asyncio
async def test_smoke_analytics(mock_session):
    async def view():
        # Patch session globally for this view
        with patch("docuflow.features.analytics.view.Session", return_value=mock_session):
            await analytics_view(mock_session)

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("Analytics")


@pytest.mark.asyncio
async def test_smoke_reports():
    sys = MagicMock()
    sys.generate_html_preview.return_value = "<html>Test</html>"

    async def view():
        await ReportsView(sys).render_portal()

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("Intelligence")


@pytest.mark.asyncio
async def test_smoke_projects():
    sys = MagicMock()
    sys.list_projects.return_value = []
    wi_sys = MagicMock()
    wi_sys.list_work_items_by_filter.return_value = []
    async with user_simulation(lambda: ProjectManagementView(sys, wi_sys).render()) as user:
        await user.open("/")
        await user.should_see("проектами")


@pytest.mark.asyncio
async def test_smoke_admin(system_provider):
    sys = MagicMock()
    sys.get_all_users.return_value = []
    sys.get_all_roles.return_value = []
    sys.get_all_workplaces.return_value = []
    sys.get_cluster_nodes = AsyncMock(return_value=[])
    layout = MagicMock()

    async def view():
        await admin_view(sys, system_provider, layout)

    async with user_simulation(view) as user:
        await user.open("/")
        await user.should_see("Registry")


@pytest.mark.asyncio
async def test_smoke_docs():
    async with user_simulation(lambda: DocumentationPortal().build_portal()) as user:
        await user.open("/")
        await user.should_see("Documentation")
