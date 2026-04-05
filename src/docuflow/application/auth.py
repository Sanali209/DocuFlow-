import json

from passlib.context import CryptContext
from sqlmodel import Session, select

from docuflow.domain.entities.identity import Role, User


class AuthService:
    """Provides decentralized authentication and identity management services.

    This service ensures that each node can verify user credentials locally using
    the synchronized database state.
    """

    def __init__(self, session: Session):
        self._session = session
        self._pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Generating a secure hash for a plain-text password."""
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifying if a plain-text password matches a previously generated hash."""
        return self._pwd_context.verify(plain_password, hashed_password)

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Validating user credentials against the local database snapshot.

        Returns:
            The User entity if authentication succeeds; otherwise, None.
        """
        statement = select(User).where(User.username == username)
        user = self._session.exec(statement).first()

        if not user:
            return None

        if self.verify_password(password, user.password_hash):
            return user

        return None

    def bootstrap_admin(self, default_password: str | None = None) -> User | None:
        """Ensuring at least one administrative user exists in the cluster.

        This method seeds a default 'admin' role and user if the database is empty,
        allowing for initial configuration of nodes and workplaces.
        
        Args:
            default_password: Admin password. If None, reads from DOCUFLOW_ADMIN_PASSWORD env var.
        """
        import os

        from loguru import logger

        if default_password is None:
            default_password = os.getenv("DOCUFLOW_ADMIN_PASSWORD")
            if not default_password:
                logger.warning("DOCUFLOW_ADMIN_PASSWORD not set, skipping admin bootstrap")
                return None
        # 1. Check if admin role exists
        role_state = select(Role).where(Role.name == "Admin")
        admin_role = self._session.exec(role_state).first()

        if not admin_role:
            admin_role = Role(
                name="Admin",
                permissions=json.dumps(["tracking", "inventory", "admin_panel", "dashboard"]),
            )
            self._session.add(admin_role)
            self._session.commit()
            self._session.refresh(admin_role)

        # 2. Check if any user exists
        user_state = select(User)
        any_user = self._session.exec(user_state).first()

        if not any_user:
            admin_user = User(
                username="admin",
                password_hash=self.hash_password(default_password),
                role_id=admin_role.id,
                allowed_workplaces="[]",  # Admin can typically access any workplace via logic
            )
            self._session.add(admin_user)
            self._session.commit()
            self._session.refresh(admin_user)
            return admin_user

        return None
