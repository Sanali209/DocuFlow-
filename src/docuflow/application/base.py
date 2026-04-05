from typing import TYPE_CHECKING

from docuflow.infrastructure.config import Config

if TYPE_CHECKING:
    pass


class BaseSystem:
    """Base class for all DocuFlow infrastructure and application systems.

    Every system (e.g., FileBus, Coordination, Inventory) inherits from this
    to ensure a consistent interface for configuration and lifecycle hooks.

    Architecture Logic:
    - Systems are 'Resource Containers' that handle a specific domain.
    - They are managed by the DI container but unified via this base class.
    """

    def __init__(self, config: Config):
        self._config = config

    @property
    def config(self) -> Config:
        """Access the 'cold' boot configuration (e.g., paths, credentials)."""
        return self._config

    async def on_startup(self) -> None:
        """Async lifecycle hook: system start."""
        pass

    async def on_shutdown(self) -> None:
        """Async lifecycle hook: system stop."""
        pass
