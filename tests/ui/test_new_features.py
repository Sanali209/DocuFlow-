from unittest.mock import MagicMock

import pytest
from nicegui import ui
from nicegui.testing import user_simulation
from sqlmodel import Session

from docuflow.domain.entities.production import WorkItem, WorkItemStatus
from docuflow.features.task_board.view import TaskBoardView
from docuflow.features.work_items.view import WorkItemsView


@pytest.fixture
def mock_wi_system():
    sys = MagicMock()
    sys.list_work_items_by_filter.return_value = [
        WorkItem(
            id=1,
            folder_name="TEST-ORDER",
            project_id=1,
            status=WorkItemStatus.NEW,
            folder_path="/test",
        )
    ]
    sys.retrieve_work_item.return_value = sys.list_work_items_by_filter.return_value[0]
    sys.db_session = MagicMock()
    return sys


@pytest.fixture
def mock_task_system():
    sys = MagicMock()
    sys.get_bucket.return_value = []
    return sys


@pytest.fixture
def system_provider():
    async def provider(stype):
        return MagicMock()

    return provider


@pytest.mark.asyncio
@pytest.mark.usefixtures("ui_context")
async def test_work_items_view_rendering(mock_wi_system, system_provider):
    """Smoke test for Work Items screen."""
    preset_sys = MagicMock()

    render_func = lambda: WorkItemsView(
        mock_wi_system, preset_sys, system_provider=system_provider
    ).render()

    async with user_simulation(render_func) as user:
        await user.open("/")
        # Check for presence of filter components
        await user.should_see("Поиск")
        # Check for presence of the Table component itself
        assert any(isinstance(e, ui.table) for e in user._gather_elements())


@pytest.mark.asyncio
@pytest.mark.usefixtures("ui_context")
async def test_task_board_operator_view(mock_task_system, system_provider):
    """Verify Task Board renders node selector and bucket."""
    session = MagicMock(spec=Session)
    preset_sys = MagicMock()
    admin_sys = MagicMock()
    admin_sys.get_all_workplaces.return_value = []

    view_func = lambda: TaskBoardView(
        session=session,
        system=mock_task_system,
        preset_system=preset_sys,
        admin_system=admin_sys,
        role="operator",
        node_id="LASER_1",
        system_provider=system_provider,
    ).render()

    async with user_simulation(view_func) as user:
        await user.open("/")
        await user.should_see("Рабочее место:")
        await user.should_see("Корзина пуста")


@pytest.mark.asyncio
@pytest.mark.usefixtures("ui_context")
async def test_task_board_role_switch(mock_task_system, system_provider):
    """Verify role switcher exists and works."""
    session = MagicMock(spec=Session)
    preset_sys = MagicMock()
    admin_sys = MagicMock()
    admin_sys.get_all_workplaces.return_value = []

    view = TaskBoardView(
        session=session,
        system=mock_task_system,
        preset_system=preset_sys,
        admin_system=admin_sys,
        system_provider=system_provider,
    )

    async with user_simulation(lambda: view.render()) as user:
        await user.open("/")
        await user.should_see("Роль:")
        await user.should_see("Оператор")
        await user.should_see("Бригадир")
