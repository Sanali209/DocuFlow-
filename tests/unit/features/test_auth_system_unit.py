"""TDD Tests for AuthSystem.

Coverage target: features/auth/system.py
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from docuflow.domain.entities.identity import Role, User
from docuflow.features.auth.system import AuthSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def auth_system():
    """Provide an AuthSystem backed by an in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        config = Config()
        system = AuthSystem(config, session)
        yield system


class TestPasswordHashing:
    """RED: AuthSystem should hash and verify passwords securely."""

    def test_hash_password_returns_different_string(self, auth_system):
        password = "secret123"
        hashed = auth_system.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_with_correct_password(self, auth_system):
        password = "secret123"
        hashed = auth_system.hash_password(password)
        assert auth_system.verify_password(password, hashed) is True

    def test_verify_password_with_wrong_password(self, auth_system):
        password = "secret123"
        hashed = auth_system.hash_password(password)
        assert auth_system.verify_password("wrong", hashed) is False

    def test_verify_password_with_different_hash(self, auth_system):
        # Two hashes of the same password should both verify
        password = "secret123"
        hashed1 = auth_system.hash_password(password)
        hashed2 = auth_system.hash_password(password)
        assert hashed1 != hashed2  # Salting
        assert auth_system.verify_password(password, hashed1) is True
        assert auth_system.verify_password(password, hashed2) is True


class TestAuthenticateUser:
    """RED: authenticate_user should validate credentials against DB."""

    async def test_authenticate_existing_user(self, auth_system):
        # Arrange: create role and user
        role = Role(name="User", permissions="[]")
        auth_system.db_session.add(role)
        auth_system.db_session.commit()
        auth_system.db_session.refresh(role)

        user = User(
            username="alice",
            password_hash=auth_system.hash_password("wonderland"),
            role_id=role.id,
            allowed_workplaces="[]",
        )
        auth_system.db_session.add(user)
        auth_system.db_session.commit()

        # Act
        result = await auth_system.authenticate_user("alice", "wonderland")

        # Assert
        assert result is not None
        assert result.username == "alice"

    async def test_authenticate_wrong_password(self, auth_system):
        role = Role(name="User", permissions="[]")
        auth_system.db_session.add(role)
        auth_system.db_session.commit()
        auth_system.db_session.refresh(role)

        user = User(
            username="alice",
            password_hash=auth_system.hash_password("wonderland"),
            role_id=role.id,
            allowed_workplaces="[]",
        )
        auth_system.db_session.add(user)
        auth_system.db_session.commit()

        result = await auth_system.authenticate_user("alice", "wrongpassword")
        assert result is None

    async def test_authenticate_nonexistent_user(self, auth_system):
        result = await auth_system.authenticate_user("nobody", "anypass")
        assert result is None


class TestGetOrCreateAdmin:
    """RED: get_or_create_admin should bootstrap admin role and user."""

    def test_creates_admin_role_when_missing(self, auth_system):
        auth_system.get_or_create_admin("adminpass")
        role = auth_system.db_session.exec(select(Role).where(Role.name == "Админ")).first()
        assert role is not None
        assert role.permissions == '["*:full"]'

    def test_creates_admin_user_when_missing(self, auth_system):
        admin = auth_system.get_or_create_admin("adminpass")
        assert admin.username == "admin"
        assert auth_system.verify_password("adminpass", admin.password_hash) is True

    def test_uses_default_password_when_none_provided(self, auth_system):
        admin = auth_system.get_or_create_admin()
        assert auth_system.verify_password("admin", admin.password_hash) is True

    def test_does_not_duplicate_on_second_call(self, auth_system):
        admin1 = auth_system.get_or_create_admin("pass1")
        admin2 = auth_system.get_or_create_admin("pass2")
        assert admin1.id == admin2.id
        # Password should stay from first creation
        assert auth_system.verify_password("pass1", admin2.password_hash) is True


class TestBootstrapAdmin:
    """RED: bootstrap_admin is legacy alias for get_or_create_admin."""

    def test_returns_same_as_get_or_create_admin(self, auth_system):
        admin1 = auth_system.get_or_create_admin("mypass")
        admin2 = auth_system.bootstrap_admin("mypass")
        assert admin1.id == admin2.id


class TestEnsureDefaultWorkplace:
    """RED: ensure_default_workplace should create default workplace if absent."""

    def test_creates_default_workplace(self, auth_system):
        from docuflow.domain.entities.identity import Workplace
        from docuflow.infrastructure import constants

        auth_system.ensure_default_workplace()
        wp = auth_system.db_session.exec(
            select(Workplace).where(Workplace.node_id == constants.DEFAULT_WORKPLACE_ID)
        ).first()
        assert wp is not None
        assert wp.name == constants.DEFAULT_WORKPLACE_NAME

    def test_idempotent_second_call(self, auth_system):
        from docuflow.domain.entities.identity import Workplace
        from docuflow.infrastructure import constants

        auth_system.ensure_default_workplace()
        auth_system.ensure_default_workplace()
        count = len(
            auth_system.db_session.exec(
                select(Workplace).where(Workplace.node_id == constants.DEFAULT_WORKPLACE_ID)
            ).all()
        )
        assert count == 1
