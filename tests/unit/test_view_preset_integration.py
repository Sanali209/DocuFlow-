"""Tests for ViewPreset integration with FilterPanel."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.features.admin.system import AdminSystem
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.security import HMACSigner


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


@pytest.fixture(name="admin_system")
def admin_system_fixture(session):
    config = Config(node_id="test_node")
    signer = HMACSigner(config.storage_secret)
    from unittest.mock import MagicMock

    orch = MagicMock()
    return AdminSystem(session, orch, signer, config)


def test_create_view_preset(admin_system):
    """AdminSystem should create and persist a ViewPreset."""
    preset = admin_system.create_view_preset(
        view_name="task_board",
        name="Срочные",
        filters_json='{"urgent": true}',
        user_id="u1",
    )
    assert preset.id is not None
    assert preset.name == "Срочные"
    assert preset.filters_json == '{"urgent": true}'


def test_get_view_presets(admin_system):
    """AdminSystem should return presets for a user."""
    admin_system.create_view_preset("task_board", "Preset 1", "{}", "u1")
    admin_system.create_view_preset("task_board", "Preset 2", "{}", "u1")
    admin_system.create_view_preset("task_board", "Other user", "{}", "u2")

    presets = admin_system.get_view_presets(user_id="u1")
    assert len(presets) == 2


def test_delete_view_preset(admin_system):
    """AdminSystem should delete a preset by ID."""
    preset = admin_system.create_view_preset("task_board", "ToDelete", "{}", "u1")
    admin_system.delete_view_preset(preset.id)

    presets = admin_system.get_view_presets(user_id="u1")
    assert len(presets) == 0
