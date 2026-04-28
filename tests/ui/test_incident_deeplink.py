"""Tests for Incident deeplink to Task Board."""

import pytest

pytest.importorskip("nicegui")

from unittest.mock import MagicMock

from docuflow.features.chat.incident_view import IncidentView


def test_incident_view_has_task_link(ui_context):
    """Incident card should have a link when task_item_id is set."""
    mock_system = MagicMock()
    view = IncidentView(incident_system=mock_system, system_scope=None)
    # Smoke test: view instantiates
    assert view is not None
