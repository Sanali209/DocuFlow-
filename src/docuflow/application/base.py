from typing import Any

from sqlalchemy import Select, func
from sqlmodel import Session, select

from docuflow.infrastructure.config import Config


class BaseSystem:
    """Base class for all DocuFlow infrastructure and application systems.

    Every system (e.g., FileBus, Coordination, Inventory) inherits from this
    to ensure a consistent interface for configuration and lifecycle hooks.

    Architecture Logic:
    - Systems are 'Resource Containers' that handle a specific domain.
    - They are managed by the DI container but unified via this base class.
    """

    def __init__(self, config: Config, session: Session | None = None) -> None:
        self._config: Config = config
        self.session: Session | None = session

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

    # --- CRUD Helpers ---

    def find_one(self, model: type[Any], **filters: Any) -> Any | None:
        """Return the first row matching all filters, or None."""
        stmt: Select = select(model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(model, key) == value)
        return self.db_session.exec(stmt).first()

    def find_all(self, model: type[Any], **filters: Any) -> list[Any]:
        """Return all rows matching the filters."""
        stmt: Select = select(model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(model, key) == value)
        return list(self.db_session.exec(stmt).all())

    def save(self, obj: Any, refresh: bool = True) -> Any:
        """Persist an object and optionally refresh it from the DB."""
        self.db_session.add(obj)
        self.db_session.commit()
        if refresh:
            self.db_session.refresh(obj)
        return obj

    def delete(self, obj: Any) -> None:
        """Remove an object from the database."""
        self.db_session.delete(obj)
        self.db_session.commit()

    def count(self, model: type[Any], **filters: Any) -> int:
        """Return the number of rows matching the filters."""
        stmt: Select = select(func.count()).select_from(model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(model, key) == value)
        return self.db_session.exec(stmt).one() or 0

    # --- Lifecycle Hooks ---

    async def on_startup(self) -> None:
        """Async lifecycle hook: system start."""
        pass

    async def on_shutdown(self) -> None:
        """Async lifecycle hook: system stop."""
        pass
