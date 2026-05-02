"""Tests for ViewPreset integration with FilterPanel."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.features.view_presets.system import ViewPresetSystem
from docuflow.infrastructure.config import Config


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


@pytest.fixture(name="preset_system")
def preset_system_fixture(session):
    config = Config(node_id="test_node")
    return ViewPresetSystem(config, session)


def test_create_view_preset(preset_system):
    """ViewPresetSystem should create and persist a ViewPreset."""
    preset = preset_system.create(
        view_name="task_board",
        name="Срочные",
        filters_json={"urgent": True},
        user_id="u1",
    )
    assert preset.id is not None
    assert preset.name == "Срочные"
    assert "urgent" in preset.filters_json


def test_list_view_presets(preset_system):
    """ViewPresetSystem should return presets for a view and user."""
    preset_system.create("task_board", "u1", "Preset 1", {})
    preset_system.create("task_board", "u1", "Preset 2", {})
    preset_system.create("task_board", "u2", "Other user", {})

    presets = preset_system.list(view_name="task_board", user_id="u1")
    assert len(presets) == 2


def test_delete_view_preset(preset_system):
    """ViewPresetSystem should delete a preset by ID."""
    preset = preset_system.create("task_board", "u1", "ToDelete", {})
    preset_system.delete_preset(preset.id, user_id="u1")

    presets = preset_system.list(view_name="task_board", user_id="u1")
    assert len(presets) == 0
