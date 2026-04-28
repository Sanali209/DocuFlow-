"""Tests for ViewState persistence in HierarchyTable."""

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import ViewState
from docuflow.lib.widgets.hierarchy_table import HierarchyTable


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


def test_hierarchy_table_get_expansion_state_default(session):
    """Default expansion state should be True when no ViewState exists."""
    table = HierarchyTable(user_id="u1", view_name="test", system_scope=None)
    assert table._get_expansion_state(session, "project", 1) is True


def test_hierarchy_table_save_and_load_expansion_state(session):
    """Saving expansion state should persist to DB and load back."""
    table = HierarchyTable(user_id="u1", view_name="test", system_scope=None)

    # Save collapsed state
    table._save_expansion_state(session, "project", 1, False)

    # Should load as collapsed
    assert table._get_expansion_state(session, "project", 1) is False

    # Different entity should still be default (True)
    assert table._get_expansion_state(session, "project", 2) is True


def test_hierarchy_table_update_existing_expansion_state(session):
    """Updating existing ViewState should modify, not create duplicate."""
    table = HierarchyTable(user_id="u1", view_name="test", system_scope=None)

    table._save_expansion_state(session, "project", 1, False)
    table._save_expansion_state(session, "project", 1, True)

    assert table._get_expansion_state(session, "project", 1) is True

    # Should be only one record
    states = list(session.exec(select(ViewState)).all())
    assert len(states) == 1
    assert states[0].is_expanded is True


def test_hierarchy_table_different_users_isolated(session):
    """ViewState should be isolated per user."""
    table_u1 = HierarchyTable(user_id="u1", view_name="test", system_scope=None)
    table_u2 = HierarchyTable(user_id="u2", view_name="test", system_scope=None)

    table_u1._save_expansion_state(session, "project", 1, False)

    assert table_u1._get_expansion_state(session, "project", 1) is False
    assert table_u2._get_expansion_state(session, "project", 1) is True


def test_hierarchy_table_different_views_isolated(session):
    """ViewState should be isolated per view."""
    table_v1 = HierarchyTable(user_id="u1", view_name="view1", system_scope=None)
    table_v2 = HierarchyTable(user_id="u1", view_name="view2", system_scope=None)

    table_v1._save_expansion_state(session, "project", 1, False)

    assert table_v1._get_expansion_state(session, "project", 1) is False
    assert table_v2._get_expansion_state(session, "project", 1) is True
