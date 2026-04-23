"""TDD Tests for SettingsRegistry as unified settings repository."""

from unittest.mock import MagicMock

import pytest
from pydantic import Field

from docuflow.domain.settings import BaseModuleSettings, SettingsRegistry


class TestModuleSettings(BaseModuleSettings):
    """Test module settings schema."""

    test_field: str = Field(default="default_value", json_schema_extra={"scope": "global"})
    test_int: int = Field(default=42, json_schema_extra={"scope": "local"})


@pytest.fixture
def fresh_registry():
    """Create a fresh registry instance for each test."""
    reg = SettingsRegistry()
    reg._admin = None  # Reset admin reference
    return reg


@pytest.fixture
def mock_admin_system():
    """Create a mock admin system."""
    admin = MagicMock()
    admin.get_node_settings.return_value = {"test_field": "from_db", "test_int": "123"}
    return admin


def test_registry_register_and_get_schema(fresh_registry):
    """RED: Registry should register and return module schemas."""
    # Register module
    fresh_registry.register("test_module", TestModuleSettings)

    # Get schema
    schema = fresh_registry.get_schema("test_module")
    assert schema == TestModuleSettings

    # Get all modules
    modules = fresh_registry.get_all_modules()
    assert "test_module" in modules


def test_registry_get_fields_by_scope(fresh_registry):
    """RED: Registry should filter fields by scope."""
    fresh_registry.register("test_module", TestModuleSettings)

    global_fields = fresh_registry.get_fields_by_scope("test_module", "global")
    assert "test_field" in global_fields
    assert "test_int" not in global_fields

    local_fields = fresh_registry.get_fields_by_scope("test_module", "local")
    assert "test_int" in local_fields
    assert "test_field" not in local_fields


def test_registry_get_module_settings_without_admin(fresh_registry):
    """RED: get_module_settings should return empty dict without admin_system."""
    fresh_registry.register("test_module", TestModuleSettings)

    settings = fresh_registry.get_module_settings("node_01", "test_module")
    assert settings == {}


def test_registry_get_module_settings_with_admin(fresh_registry, mock_admin_system):
    """RED: get_module_settings should read from admin_system."""
    fresh_registry.register("test_module", TestModuleSettings)
    fresh_registry.init(mock_admin_system)

    settings = fresh_registry.get_module_settings("node_01", "test_module")

    # Verify admin_system was called
    mock_admin_system.get_node_settings.assert_called_once_with("node_01", "test_module")
    assert settings == {"test_field": "from_db", "test_int": "123"}


def test_registry_update_module_setting(fresh_registry, mock_admin_system):
    """RED: update_module_setting should call admin_system."""
    fresh_registry.register("test_module", TestModuleSettings)
    fresh_registry.init(mock_admin_system)

    fresh_registry.update_module_setting("node_01", "test_module", "test_field", "new_value")

    # Verify admin_system was called
    mock_admin_system.update_node_setting.assert_called_once_with(
        "node_01", "test_module", "test_field", "new_value"
    )


def test_registry_get_settings_object(fresh_registry, mock_admin_system):
    """RED: get_settings_object should return populated settings object."""
    fresh_registry.register("test_module", TestModuleSettings)
    fresh_registry.init(mock_admin_system)

    settings_obj = fresh_registry.get_settings_object("node_01", "test_module")

    assert isinstance(settings_obj, TestModuleSettings)
    assert settings_obj.test_field == "from_db"
    assert settings_obj.test_int == 123


def test_registry_get_settings_object_without_admin(fresh_registry):
    """RED: get_settings_object should return None without admin_system."""
    fresh_registry.register("test_module", TestModuleSettings)

    settings_obj = fresh_registry.get_settings_object("node_01", "test_module")
    assert settings_obj is None


def test_registry_get_settings_object_unknown_module(fresh_registry, mock_admin_system):
    """RED: get_settings_object should return None for unknown module."""
    fresh_registry.init(mock_admin_system)

    settings_obj = fresh_registry.get_settings_object("node_01", "unknown_module")
    assert settings_obj is None
