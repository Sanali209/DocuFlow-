from typing import TYPE_CHECKING, Any

from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.settings import Setting

if TYPE_CHECKING:
    from docuflow.infrastructure.config import Config


class SettingsSystem(BaseSystem):
    """Runtime settings implementation.
    Fetches hot configuration directly from SQLite.
    """
    def __init__(self, config: 'Config', session: Session):
        super().__init__(config)
        self._session = session

    async def get(self, key: str, default: Any = None) -> Any:
        """Fetch a dynamic setting by key."""
        statement = select(Setting).where(Setting.key == key)
        result = self._session.exec(statement).first()
        if not result:
            return default
        return result.value

    async def set(self, key: str, value: Any, description: str | None = None) -> None:
        """Update or create a dynamic setting."""
        statement = select(Setting).where(Setting.key == key)
        setting = self._session.exec(statement).first()

        if not setting:
            setting = Setting(key=key, value=value, description=description)
        else:
            setting.value = value
            if description:
                setting.description = description

        self._session.add(setting)
        self._session.commit()
        self._session.refresh(setting)
