"""Tests for CompleteTaskDialog widget."""

import pytest

pytest.importorskip("nicegui")

from docuflow.lib.widgets.complete_task_dialog import CompleteTaskDialog


def test_complete_task_dialog_instantiates():
    """Smoke test: CompleteTaskDialog can be created."""
    dialog = CompleteTaskDialog(
        task_id=1,
        qty_produced=10,
        on_complete=lambda **kw: None,
        system_scope=None,
    )
    assert dialog is not None
    assert dialog.task_id == 1
    assert dialog.qty_produced == 10


def test_complete_task_dialog_default_new_pallet():
    """Default selection should be 'create new pallet'."""
    dialog = CompleteTaskDialog(
        task_id=1,
        qty_produced=10,
        on_complete=lambda **kw: None,
        system_scope=None,
    )
    # Default: create_new = True
    assert dialog.create_new is True
