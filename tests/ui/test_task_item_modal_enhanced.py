"""Tests for enhanced TaskItemModal."""

import pytest

pytest.importorskip("nicegui")

from docuflow.domain.entities.production import TaskItem
from docuflow.lib.widgets.entity_modals import TaskItemModal


def test_task_item_modal_accepts_action_callbacks():
    """
    TaskItemModal must accept separate callbacks for start, pause,
    complete, and incident actions instead of a single generic on_action.
    """
    task = TaskItem(file_name="test.gnc", file_path="test.gnc")

    started = []
    paused = []
    completed = []
    incidented = []

    def on_start(task_item_id: int) -> None:
        started.append(task_item_id)

    def on_pause(task_item_id: int) -> None:
        paused.append(task_item_id)

    def on_complete(task_item_id: int, create_new: bool, selected_pallet_id: int | None) -> None:
        completed.append((task_item_id, create_new, selected_pallet_id))

    def on_incident(task_item_id: int) -> None:
        incidented.append(task_item_id)

    m = TaskItemModal(
        task,
        on_start=on_start,
        on_pause=on_pause,
        on_complete=on_complete,
        on_incident=on_incident,
        system_scope=None,
    )

    assert m.on_start is on_start
    assert m.on_pause is on_pause
    assert m.on_complete is on_complete
    assert m.on_incident is on_incident


def test_task_item_modal_stores_task_item():
    """TaskItemModal must store the task_item reference."""
    task = TaskItem(file_name="test.gnc", file_path="test.gnc")
    m = TaskItemModal(task, system_scope=None)
    assert m.task_item is task
