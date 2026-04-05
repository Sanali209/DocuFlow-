import json

from passlib.context import CryptContext
from sqlmodel import Session, select

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
        super().__init__(config)
        self.db_session = db_session
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
        statement = select(User).where(User.username == username)
        user = self.db_session.exec(statement).first()

        if not user or not self.verify_password(password, user.password_hash):
            return None

        return user

    def bootstrap_admin(self, default_password: str = "docuflow_admin") -> User | None:
        """
        Ensures at least one administrative user exists in the cluster.
        Symmetry: Every node must be able to bootstrap an initial admin if empty.
        """
        # 1. Check if the administrative role exists
        admin_role_name = "Админ"
        role_statement = select(Role).where(Role.name == admin_role_name)
        admin_role = self.db_session.exec(role_statement).first()

        if not admin_role:
            admin_role = Role(
                name=admin_role_name,
                permissions=json.dumps(["*:full"]),  # Master permission
            )
            self.db_session.add(admin_role)
            self.db_session.commit()
            self.db_session.refresh(admin_role)

        # 2. Check if any user is registered
        user_statement = select(User)
        existing_user = self.db_session.exec(user_statement).first()

        if not existing_user:
            admin_user = User(
                username="admin",
                password_hash=self.hash_password(default_password),
                role_id=admin_role.id,
                allowed_workplaces="[]",
            )
            self.db_session.add(admin_user)
            self.db_session.commit()
            self.db_session.refresh(admin_user)
            return admin_user

        return None
