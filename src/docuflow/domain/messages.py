from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CommandType(str, Enum):
    """Enumeration of supported P2P cluster commands.

    Commands define the intent of a request sent over the File Bus.
    """

    UPSERT_USER = "UPSERT_USER"
    DELETE_USER = "DELETE_USER"
    UPSERT_ROLE = "UPSERT_ROLE"
    DELETE_ROLE = "DELETE_ROLE"
    UPSERT_SETTING = "UPSERT_SETTING"
    UPSERT_WORKPLACE = "UPSERT_WORKPLACE"
    REVOKE_PERMISSIONS = "REVOKE_PERMISSIONS"
    SYNC_WORKPLACE = "SYNC_WORKPLACE"
    FORCE_STEP_DOWN = "FORCE_STEP_DOWN"
    RECONCILE_SNAPSHOT = "RECONCILE_SNAPSHOT"


class P2PPayload(BaseModel):
    """The domain-specific content of a P2P message."""

    command: CommandType
    data: dict[str, Any] = Field(default_factory=dict)


class P2PMessage(BaseModel):
    """Cryptographically secured envelope for all File Bus communication.

    Every .json file placed in the BUS/INBOX must conform to this schema
    to be accepted by the SecureDispatcher.
    """

    sender_id: str  # Originating Node ID
    sequence: int = Field(default=0)  # Causal ordering / Replay protection
    timestamp: float  # Wall-clock time of creation
    payload: P2PPayload  # The actual command and data
    signature: str | None = None  # HMAC-SHA256 hex digest

    def to_signable_content(self) -> str:
        """Generate a stable string representation for HMAC calculation.

        This excludes the 'signature' field itself.
        """
        # We exclude signature for hashing.
        # Using model_dump_json ensures stable ordering if configured,
        # but for simplicity, we'll use a controlled dictionary exclusion.
        data = self.model_dump(exclude={"signature"})
        # Sort keys to ensure consistent hashing across different platforms/versions
        import json

        return json.dumps(data, sort_keys=True)
