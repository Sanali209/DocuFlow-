from unittest.mock import MagicMock

from docuflow.domain.entities.identity import Role
from docuflow.features.admin.system import AdminSystem


def test_admin_role_delete_protection():
    """Verify that the core 'admin' role cannot be deleted."""
    session_mock = MagicMock()
    # Simulate finding an existing 'admin' role
    admin_role = Role(id=1, name="admin", permissions='["admin_panel"]')
    session_mock.exec.return_value.first.return_value = admin_role

    orchestrator_mock = MagicMock()
    admin_system = AdminSystem(
        session=session_mock, orchestrator=orchestrator_mock, signer=MagicMock(), config=MagicMock()
    )

    # Act: Attempt to delete the admin role
    admin_system.delete_role("admin")

    # Assert: session.delete and orchestrator.broadcast SHOULD NOT be called
    assert not session_mock.delete.called, (
        "CRITICAL: 'admin' role deletion should be blocked in session"
    )
    assert not orchestrator_mock.broadcast_command.called, (
        "CRITICAL: 'admin' role deletion should not be broadcast"
    )


def test_admin_role_upsert_protection():
    """Verify that core 'admin' permissions cannot be modified via ad-hoc upsert."""
    session_mock = MagicMock()
    admin_role = Role(id=1, name="admin", permissions='["admin_panel"]')
    session_mock.exec.return_value.first.return_value = admin_role

    orchestrator_mock = MagicMock()
    admin_system = AdminSystem(
        session=session_mock, orchestrator=orchestrator_mock, signer=MagicMock(), config=MagicMock()
    )

    # Act: Attempt to change admin permissions
    admin_system.upsert_role("admin", ["hacker_access"])

    # Assert: We expect it to ignore the update or keep old permissions
    # In this failure test, we'll assert that it was NOT broadcast with new perms
    # (Checking that the implementation currently FAILS to block this)
    assert not orchestrator_mock.broadcast_command.called, (
        "CRITICAL: 'admin' role modification should not be broadcast"
    )
