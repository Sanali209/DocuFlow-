import datetime
from sqlmodel import Field, SQLModel

class BaseEntity(SQLModel):
    """Common foundation for all persistent domain entities.
    
    Provides standard primary keys and audit timestamps (created_at, updated_at)
    to facilitate Last-Write-Wins (LWW) conflict resolution in the P2P cluster.
    """
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
