"""Tests for FilterPanel widget."""

import pytest

pytest.importorskip("nicegui")

from docuflow.lib.widgets.filter_panel import FilterPanel


def test_filter_panel_instantiates():
    """Smoke test: FilterPanel can be created."""
    panel = FilterPanel(on_apply=lambda f: None, system_scope=None)
    assert panel is not None


def test_filter_panel_default_filters():
    """Default filters should be empty."""
    panel = FilterPanel(on_apply=lambda f: None, system_scope=None)
    assert panel.filters == {}


def test_filter_panel_apply_callback():
    """Apply button should trigger on_apply with current filters."""
    received = {}

    def capture(filters):
        received.update(filters)

    panel = FilterPanel(on_apply=capture, system_scope=None)
    panel.filters = {"project_id": 1, "status": "in_progress"}
    panel._apply()

    assert received.get("project_id") == 1
    assert received.get("status") == "in_progress"


def test_filter_panel_reset():
    """Reset should clear all filters and trigger on_apply with empty dict."""
    received = None

    def capture(filters):
        nonlocal received
        received = filters

    panel = FilterPanel(on_apply=capture, system_scope=None)
    panel.filters = {"project_id": 1}
    panel._reset()

    assert panel.filters == {}
    assert received == {}
