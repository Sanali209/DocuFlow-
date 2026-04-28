import pytest

pytest.importorskip("nicegui")

from docuflow.features.task_board.view import TaskBoardView


def test_task_board_view_has_refresh_attributes():
    view = TaskBoardView(system_scope=None, user="test")
    assert hasattr(view, "_refresh_timer")
    assert view._refresh_timer is None
    assert hasattr(view, "_last_data_hash")
    assert view._last_data_hash is None


def test_task_board_view_default_user_and_role():
    view = TaskBoardView(system_scope=None)
    assert view.user == "admin"
    assert view.role == "operator"
    assert view.node_id is None


def test_task_board_view_custom_params():
    view = TaskBoardView(
        system_scope=None,
        user="operator_1",
        node_id="LASER_1",
        role="foreman",
        filter_work_item_id=42,
    )
    assert view.user == "operator_1"
    assert view.node_id == "LASER_1"
    assert view.role == "foreman"
    assert view.filter_work_item_id == 42
