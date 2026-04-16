import pytest
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.identity import Role
from docuflow.features.auth.system import AuthSystem
from docuflow.infrastructure.config import Config

pytest.importorskip("passlib")


@pytest.fixture(name="config")
def config_fixture():
    return Config(node_id="TEST_NODE")


@pytest.fixture(name="session")
def session_fixture():
    """Providing an in-memory SQLite session for isolated auth testing."""
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_password_hashing(session, config):
    """Verifying that passwords are appropriately hashed and non-reversible."""
    auth = AuthSystem(config, session)
    password = "secret_password"
    hashed = auth._pwd_context.hash(password)

    assert hashed != password
    assert auth._pwd_context.verify(password, hashed) is True
    assert auth._pwd_context.verify("wrong_password", hashed) is False


def test_admin_bootstrapping(session, config):
    """Confirming that the system can seed an initial admin user on first run."""
    auth = AuthSystem(config, session)

    # Initial state is empty (except what AuthSystem might create in __init__ if we aren't careful,
    # but here we call it manually)
    admin = auth.get_or_create_admin()

    assert admin is not None
    assert admin.username == "admin"
    # Default password for auto-seeded admin is 'admin' in AuthSystem
    assert auth._pwd_context.verify("admin", admin.password_hash) is True

    # Role check
    role = session.get(Role, admin.role_id)
    assert role is not None
    assert role.name == "Admin"


@pytest.mark.asyncio
async def test_authentication_flow(session, config):
    """Verifying the standard login flow against the synchronized local database."""
    auth = AuthSystem(config, session)
    auth.get_or_create_admin()  # seeds admin with password 'admin'

    # Successful login
    user = await auth.authenticate_user("admin", "admin")
    assert user is not None
    assert user.username == "admin"

    # Failed login (wrong password)
    failed_user = await auth.authenticate_user("admin", "wrong")
    assert failed_user is None

    # Failed login (non-existent user)
    missing_user = await auth.authenticate_user("ghost", "any")
    assert missing_user is None
