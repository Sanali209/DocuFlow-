"""Tests for IncidentView project/work_item filters."""

import pytest

pytest.importorskip("nicegui")

from docuflow.domain.entities.production import IncidentLog
from docuflow.features.chat.incident_view import IncidentView


class FakeIncidentSystem:
    """Stub incident system for UI tests."""

    def __init__(self, incidents):
        self._incidents = incidents

    def get_active(self):
        return [i for i in self._incidents if not i.resolved_at]

    def get_recent_history(self, limit=10):
        return [i for i in self._incidents if i.resolved_at][:limit]


def test_incident_view_accepts_project_filter():
    """IncidentView must support filtering by project_id."""
    incidents = [
        IncidentLog(
            incident_type="B1", description="D1", reported_by="u1",
            assigned_group="Foreman", project_id=1,
        ),
        IncidentLog(
            incident_type="B2", description="D2", reported_by="u1",
            assigned_group="Maintenance", project_id=2,
        ),
    ]
    system = FakeIncidentSystem(incidents)
    view = IncidentView(system, current_user="foreman", system_scope=None)

    # Default: no project filter
    assert view.active_project_filter is None
    assert view.active_work_item_filter is None


def test_incident_view_filter_by_project():
    """Setting active_project_filter should exclude unrelated incidents."""
    incidents = [
        IncidentLog(
            incident_type="B1", description="D1", reported_by="u1",
            assigned_group="Foreman", project_id=1,
        ),
        IncidentLog(
            incident_type="B2", description="D2", reported_by="u1",
            assigned_group="Foreman", project_id=2,
        ),
    ]
    system = FakeIncidentSystem(incidents)
    view = IncidentView(system, current_user="foreman", system_scope=None)
    view.active_project_filter = 1

    active = system.get_active()
    filtered = [i for i in active if view._matches_filters(i)]
    assert len(filtered) == 1
    assert filtered[0].incident_type == "B1"
