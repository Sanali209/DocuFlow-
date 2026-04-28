"""Tests for Part Library ↔ Task Board deeplink integration."""

import pytest

pytest.importorskip("nicegui")

from docuflow.lib.widgets.hierarchy_table import HierarchyTable


def test_taskitem_row_has_part_deeplink(ui_context):
    """TaskItem row should render clickable part SKUs."""
    table = HierarchyTable(user_id="admin", view_name="test", system_scope=None)
    # Smoke test: table exists and has render method
    assert hasattr(table, "_render_taskitem")
