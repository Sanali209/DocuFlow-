import logging
from typing import Any, ClassVar, Optional

from pydantic import BaseModel


class BaseModuleSettings(BaseModel):
    """Base class for all schema-driven module configurations.

    This class enables **Declarative P2P Configuration**. Modules define
    their required parameters as Pydantic fields.

    Visibility Scopes:
    - `global`: Settings synchronized across all nodes via the Master database.
    - `local`: Settings specific to the current node/hardware (e.g., COM ports).

    Usage:
        >>> class MySettings(BaseModuleSettings):
        >>>     port: int = Field(..., json_schema_extra={"scope": "local"})
    """

    model_config = {"extra": "ignore", "validate_assignment": True}


class SettingsRegistry:
    """Central registry and unified repository for DocuFlow module settings.

    The registry acts as the **Cluster Control Plane's knowledge base**. It allows:
    - Discover what settings are available in the cluster.
    - Validate incoming P2P configuration updates.
    - Differentiate between global and local parameters.
    - Read and write settings from database (unified repository).
    """

    _instance: ClassVar[Optional["SettingsRegistry"]] = None
    _schemas: ClassVar[dict[str, type[BaseModuleSettings]]] = {}
    _admin: ClassVar[Any | None] = None  # AdminSystem reference for DB access

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init(self, admin_system: Any) -> None:
        """Initialize registry with admin system for database access."""
        self._admin = admin_system  # type: ignore[misc]
        logger = logging.getLogger(__name__)
        logger.info(f"SettingsRegistry.init: admin_system set to {type(admin_system).__name__}")

    def register(self, module_name: str, schema: type[BaseModuleSettings]):
        """Register a module's settings model."""
        self._schemas[module_name] = schema

    def get_schema(self, module_name: str) -> type[BaseModuleSettings] | None:
        """Retrieve the registered schema for a module."""
        return self._schemas.get(module_name)

    def get_all_modules(self) -> list[str]:
        """List all modules that have registered a settings schema."""
        return list(self._schemas.keys())

    def get_fields_by_scope(self, module_name: str, scope: str) -> list[str]:
        """Filter a module's fields based on their declared scope (global/local)."""
        schema = self.get_schema(module_name)
        if not schema:
            return []

        filtered_fields = []
        for name, field in schema.model_fields.items():
            # Check for scope in json_schema_extra
            extra_raw = field.json_schema_extra
            extra = extra_raw if isinstance(extra_raw, dict) else {}
            if extra.get("scope") == scope:
                filtered_fields.append(name)
        return filtered_fields

    def get_module_settings(self, node_id: str, module: str) -> dict[str, str]:
        """Read module settings from database for specific node."""
        if not self._admin:
            return {}
        return self._admin.get_node_settings(node_id, module)

    def update_module_setting(self, node_id: str, module: str, key: str, value: str) -> None:
        """Update module setting in database and broadcast via P2P."""
        if self._admin:
            self._admin.update_node_setting(node_id, module, key, value)

    def get_settings_object(self, node_id: str, module: str) -> BaseModuleSettings | None:
        """Get settings object populated with values from database."""
        schema = self.get_schema(module)
        if not schema:
            return None

        data = self.get_module_settings(node_id, module)
        if not data:
            # No data from database - return None instead of defaults
            return None
        return schema(**data)


# Global instance for easy access across the application
registry = SettingsRegistry()
