from sqlmodel import Session

from docuflow.infrastructure.config import Config


class BaseSystem:
    """Base class for all DocuFlow infrastructure and application systems.

    Every system (e.g., FileBus, Coordination, Inventory) inherits from this
    to ensure a consistent interface for configuration and lifecycle hooks.

    Architecture Logic:
    - Systems are 'Resource Containers' that handle a specific domain.
    - They are managed by the DI container but unified via this base class.
    """

    def __init__(self, config: Config, session: Session | None = None):
        self._config = config
        self.session = session

    @property
    def config(self) -> Config:
        """Access the 'cold' boot configuration (e.g., paths, credentials)."""
        return self._config

    @property
    def db_session(self) -> Session:
        """Access the current database session. Raises RuntimeError if not set."""
        if self.session is None:
            raise RuntimeError(
                f"System {self.__class__.__name__} accessed db_session before it was set."
            )
        return self.session

    @db_session.setter
    def db_session(self, session: Session) -> None:
        """Set the current database session."""
        self.session = session

    def set_session(self, session: Session) -> None:
        """Dynamically set or swap the session for the system."""
        self.session = session

    async def on_startup(self) -> None:
        """Async lifecycle hook: system start."""
        pass

    async def on_shutdown(self) -> None:
        """Async lifecycle hook: system stop."""
        pass
