import pytest
from pydantic import Field
from docuflow.domain.settings import SettingsRegistry, BaseModuleSettings

class MockSettings(BaseModuleSettings):
    poll_interval: int = Field(default=5, json_schema_extra={"scope": "local"})
    cluster_name: str = Field(default="DocuFlow", json_schema_extra={"scope": "global"})

def test_registry_registration():
    """Verify that modules can register their Pydantic schemas."""
    registry = SettingsRegistry()
    registry.register("mock", MockSettings)
    
    schema = registry.get_schema("mock")
    assert schema == MockSettings
    assert "mock" in registry.get_all_modules()

def test_scope_introspection():
    """Verify that we can filter settings fields by their declared scope."""
    registry = SettingsRegistry()
    registry.register("mock", MockSettings)
    
    global_fields = registry.get_fields_by_scope("mock", "global")
    assert "cluster_name" in global_fields
    assert "poll_interval" not in global_fields
    
    local_fields = registry.get_fields_by_scope("mock", "local")
    assert "poll_interval" in local_fields
    assert "cluster_name" not in local_fields
