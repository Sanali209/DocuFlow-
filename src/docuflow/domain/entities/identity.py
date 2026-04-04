from typing import List, Optional
import json
from sqlmodel import Field, Relationship
from docuflow.domain.entities.base import BaseEntity

class Workplace(BaseEntity, table=True):
    """Represents a physical machine or station (the 'Point' in authorization).
    
    Workplaces define what hardware capabilities are available on a specific node.
    """
    node_id: str = Field(index=True, unique=True)  # Physical ID (e.g. LASER_01)
    name: str                                      # Human-readable label
    allowed_modules: str = Field(default="[]")     # JSON list ["tracking", "inventory"]

    @property
    def modules_list(self) -> List[str]:
        """Convert the JSON string of allowed modules into a physical list."""
        try:
            return json.loads(self.allowed_modules)
        except (ValueError, TypeError):
            return []

class Role(BaseEntity, table=True):
    """Represents a human job function (the 'Identity' base in authorization).
    
    Roles define default permission sets for groups of users.
    """
    name: str = Field(unique=True)                  # Admin, Operator, Foreman
    permissions: str = Field(default="[]")          # JSON list ["can_edit_tasks"]
    
    # Relation: Roles have many Users
    users: List["User"] = Relationship(back_populates="role")

    @property
    def permissions_list(self) -> List[str]:
        """Convert the JSON string of permissions into a physical list."""
        try:
            return json.loads(self.permissions)
        except (ValueError, TypeError):
            return []

class User(BaseEntity, table=True):
    """Represents an individual user within the cluster.
    
    User access is validated by local logins against a synchronized database state.
    """
    username: str = Field(unique=True, index=True)
    password_hash: str
    role_id: int = Field(foreign_key="role.id")
    allowed_workplaces: str = Field(default="[]")   # JSON list of Workplace IDs

    # Relation: User belongs to a Role
    role: Optional["Role"] = Relationship(back_populates="users")

    @property
    def workplace_ids(self) -> List[int]:
        """Convert the JSON string of allowed workplace IDs into a physical list."""
        try:
            return json.loads(self.allowed_workplaces)
        except (ValueError, TypeError):
            return []

class NodeSetting(BaseEntity, table=True):
    """Represents a persistent configuration override for a specific module on a specific node.
    
    These settings are synchronized via the P2P mesh and persisted in the local node DB.
    """
    node_id: str = Field(index=True)
    module: str = Field(index=True)
    key: str = Field(index=True)
    value: str = Field(default="")  # JSON stringified value
