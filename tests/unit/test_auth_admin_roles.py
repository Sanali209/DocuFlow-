from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from docuflow.features.admin.system import AdminSyncSystem
from docuflow.features.auth.system import AuthSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def auth_system(db_session, tmp_path):
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    return AuthSystem(config, db_session)


def test_get_or_create_admin_uses_cyrillic_role(auth_system):
    """get_or_create_admin must create/find Cyrillic role 'Админ'."""
    admin = auth_system.get_or_create_admin("test_pass")
    from docuflow.domain.entities.identity import Role
    role = auth_system.db_session.get(Role, admin.role_id)
    assert role is not None
    assert role.name == "Админ", f"Expected 'Админ', got '{role.name}'"


def test_admin_sync_is_admin_handles_cyrillic(tmp_path):
    """AdminSyncSystem._is_admin must protect both 'Админ' and 'admin'."""
    engine = MagicMock()
    sync = AdminSyncSystem(engine)
    assert sync._is_admin("Админ") is True, "Cyrillic Админ must be protected"
    assert sync._is_admin("admin") is True
    assert sync._is_admin("Admin") is True
    assert sync._is_admin("ADMIN") is True
    assert sync._is_admin("operator") is False


def test_admin_sync_cannot_delete_cyrillic_admin_role(tmp_path):
    """handle_delete_role must not delete Cyrillic 'Админ' role."""
    engine = MagicMock()
    sync = AdminSyncSystem(engine)
    # Should silently skip the delete, not open a session
    sync.handle_delete_role({"name": "Админ"})
    engine.connect.assert_not_called()
