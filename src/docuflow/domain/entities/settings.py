import datetime
from typing import Any

from sqlmodel import JSON, Field, SQLModel


class Setting(SQLModel, table=True):
    """Hot configuration: dynamic settings stored in database."""
    key: str = Field(primary_key=True)
    value: Any = Field(sa_type=JSON)
    description: str | None = None
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
