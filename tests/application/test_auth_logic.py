import pytest
pytest.importorskip("passlib")
from sqlmodel import Session, SQLModel, create_engine

from docuflow.application.auth import AuthService
from docuflow.domain.entities.identity import Role, User


@pytest.fixture(name="session")
def session_fixture():
    """Providing an in-memory SQLite session for isolated auth testing."""
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_password_hashing(session):
    """Verifying that passwords are appropriately hashed and non-reversible."""
    auth = AuthService(session)
    password = "secret_password"
    hashed = auth.hash_password(password)

    assert hashed != password
    assert auth.verify_password(password, hashed) is True
    assert auth.verify_password("wrong_password", hashed) is False


def test_admin_bootstrapping(session):
    """Confirming that the system can seed an initial admin user on first run."""
    auth = AuthService(session)

    # Initial state is empty
    assert session.query(User).count() == 0

    # Bootstrap
    admin = auth.bootstrap_admin("admin_pass")

    assert admin is not None
    assert admin.username == "admin"
    assert auth.verify_password("admin_pass", admin.password_hash) is True

    # Role check
    role = session.get(Role, admin.role_id)
    assert role.name == "Admin"
    assert "admin_panel" in role.permissions


@pytest.mark.asyncio
async def test_authentication_flow(session):
    """Verifying the standard login flow against the synchronized local database."""
    auth = AuthService(session)
    auth.bootstrap_admin("p@ssword")

    # Successful login
    user = await auth.authenticate_user("admin", "p@ssword")
    assert user is not None
    assert user.username == "admin"

    # Failed login (wrong password)
    failed_user = await auth.authenticate_user("admin", "wrong")
    assert failed_user is None

    # Failed login (non-existent user)
    missing_user = await auth.authenticate_user("ghost", "any")
    assert missing_user is None
