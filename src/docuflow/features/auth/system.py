import json

from passlib.context import CryptContext
from sqlmodel import Session

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.identity import Role, User
from docuflow.infrastructure.config import Config


class AuthSystem(BaseSystem):
    """
    Provides decentralized authentication and identity management services.

    This system ensures that each workshop node can verify user credentials
    locally using the synchronized distributed database state.
    """

    def __init__(self, config: Config, db_session: Session):
        """
        Initialize the authentication engine.

        Args:
            config: System configuration.
            db_session: SQLModel session for identity verification.
        """
        super().__init__(config, db_session)
        self._pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Generating a secure hash for a plain-text password using PBKDF2."""
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifying if a plain-text password matches a previously generated hash."""
        return self._pwd_context.verify(plain_password, hashed_password)

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """
        Validates user credentials against the local database snapshot.

        Example:
            user = await system.authenticate_user("admin", "secret123")
        """
        user = self.find_one(User, username=username)

        if not user or not self.verify_password(password, user.password_hash):
            return None

        return user

    def get_or_create_admin(self, default_password: str | None = None) -> User:
        """
        Ensures at least one administrative user exists in the cluster.
        Symmetry: Every node must be able to bootstrap an initial admin if empty.

        Args:
            default_password: Admin password. Falls back to 'admin' if not provided.
        """
        # 1. Ensure Admin role exists
        admin_role = self.find_one(Role, name="Admin")
        if not admin_role:
            admin_role = self.save(
                Role(name="Admin", permissions=json.dumps(["*:full"]))
            )

        # 2. Ensure admin user exists
        admin_user = self.find_one(User, username="admin")
        if not admin_user:
            admin_user = self.save(
                User(
                    username="admin",
                    password_hash=self.hash_password(default_password or "admin"),
                    role_id=admin_role.id,
                    allowed_workplaces="[]",
                )
            )

        return admin_user

    def bootstrap_admin(self, default_password: str | None = None) -> User | None:
        """Legacy alias for get_or_create_admin."""
        return self.get_or_create_admin(default_password)

    def ensure_default_workplace(self) -> None:
        """
        Creates a default Workplace if none exists.
        Bootstrapping logic for initial node setup.
        """
        from loguru import logger

        from docuflow.domain.entities.identity import Workplace
        from docuflow.infrastructure import constants

        existing = self.find_one(Workplace, node_id=constants.DEFAULT_WORKPLACE_ID)

        if not existing:
            workplace = Workplace(
                node_id=constants.DEFAULT_WORKPLACE_ID,
                name=constants.DEFAULT_WORKPLACE_NAME,
                allowed_modules="",
            )
            try:
                self.save(workplace, refresh=False)
                logger.info(f"Created default workplace: {constants.DEFAULT_WORKPLACE_ID}")
            except Exception:
                # Handle race condition in multi-node startup
                self.db_session.rollback()
                logger.debug("Default workplace already exists (race condition handled)")
