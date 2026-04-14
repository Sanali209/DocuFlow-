import json

import pytest

from docuflow.features.core.layout import check_access, get_active_ui_modules
from docuflow.domain.entities.identity import Role, User, Workplace


@pytest.fixture
def admin_role():
    return Role(id=1, name="Admin", permissions=json.dumps(["all"]))


@pytest.fixture
def operator_role():
    return Role(id=2, name="Operator", permissions=json.dumps(["tracking"]))


@pytest.fixture
def laser_workplace():
    return Workplace(
        id=10,
        node_id="LASER_01",
        name="Laser",
        allowed_modules=json.dumps(["tracking", "inventory"]),
    )


def test_admin_access_allowed_everywhere(admin_role, laser_workplace):
    """TDD: Verify that admins can bypass workplace restrictions."""
    user = User(username="admin", role_id=admin_role.id, allowed_workplaces="[]")
    user.role = admin_role

    assert check_access(user, laser_workplace) is True
    assert get_active_ui_modules(user, laser_workplace) == {"tracking", "inventory"}


def test_operator_access_restricted_by_workplace(operator_role, laser_workplace):
    """TDD: Verify standard users are restricted to assigned workplaces."""
    # User allowed on workplace 10
    user_ok = User(username="op1", role_id=operator_role.id, allowed_workplaces="[10]")
    user_ok.role = operator_role

    # User not allowed on workplace 10
    user_fail = User(username="op2", role_id=operator_role.id, allowed_workplaces="[20]")
    user_fail.role = operator_role

    assert check_access(user_ok, laser_workplace) is True
    assert check_access(user_fail, laser_workplace) is False


def test_ui_module_intersection(operator_role, laser_workplace):
    """TDD: Verify UI modules are limited by BOTH role perms and workplace capabilities."""
    user = User(username="op1", role_id=operator_role.id, allowed_workplaces="[10]")
    user.role = operator_role

    # Operator perms: ["tracking"]
    # Workplace mods: ["tracking", "inventory"]
    # Intersection: {"tracking"}
    active = get_active_ui_modules(user, laser_workplace)
    assert active == {"tracking"}
    assert "inventory" not in active
