import pytest
from sqlmodel import Session, create_engine, SQLModel

from docuflow.domain.entities.production import IncidentLog
from docuflow.features.chat.incidents import IncidentSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def incident_system(tmp_path):
    from unittest.mock import MagicMock
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    session = Session(engine)
    return IncidentSystem(config, session, chat_system=MagicMock())


def _add_incident(session, resolved, incident_type="BREAKDOWN"):
    inc = IncidentLog(
        incident_type=incident_type,
        description="test",
        reported_by="test",
        node_id="TEST",
        resolved=resolved,
    )
    session.add(inc)
    session.flush()
    return inc


def test_get_active_failures_excludes_resolved(incident_system):
    """get_active_failures must only return incidents where resolved=False (not resolved=True)."""
    session = incident_system.db_session
    _add_incident(session, resolved=False)   # active — must be included
    _add_incident(session, resolved=True)    # resolved — must be excluded
    session.commit()

    active = incident_system.get_active_failures()
    assert len(active) == 1
    assert active[0].resolved is False


def test_get_active_failures_sorts_by_created_at(incident_system):
    """get_active_failures must sort by created_at.desc() (resolved_at is NULL for active)."""
    import datetime
    session = incident_system.db_session
    # Add two active incidents with explicit created_at values
    inc1 = IncidentLog(
        incident_type="BREAKDOWN",
        description="older",
        reported_by="test",
        node_id="TEST",
        resolved=False,
        created_at=datetime.datetime(2026, 1, 1, 10, 0, 0),
    )
    inc2 = IncidentLog(
        incident_type="DEFECT",
        description="newer",
        reported_by="test",
        node_id="TEST",
        resolved=False,
        created_at=datetime.datetime(2026, 1, 2, 10, 0, 0),
    )
    session.add(inc1)
    session.add(inc2)
    session.commit()

    active = incident_system.get_active_failures()
    assert len(active) == 2
    # Newest first
    assert active[0].description == "newer"
    assert active[1].description == "older"


def test_get_summary_stats_excludes_unresolved(incident_system):
    """get_summary_stats must only count incidents where resolved=True (not resolved=False)."""
    session = incident_system.db_session
    inc = _add_incident(session, resolved=True)
    inc.downtime_minutes = 30.0
    _add_incident(session, resolved=False)   # must be excluded
    session.commit()

    stats = incident_system.get_summary_stats()
    total = sum(stats.values())
    assert total == 30.0, f"Expected 30.0 (only resolved=True), got {total}"
