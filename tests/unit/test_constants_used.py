def test_logistics_request_tag_constant_exists():
    """LOGISTICS_REQUEST_TAG must be defined in constants."""
    from docuflow.infrastructure import constants
    assert hasattr(constants, "LOGISTICS_REQUEST_TAG")
    assert constants.LOGISTICS_REQUEST_TAG == "[LOGISTICS_REQUEST]"


def test_admin_role_names_constant_exists():
    """ADMIN_ROLE_NAMES must be defined in constants."""
    from docuflow.infrastructure import constants
    assert hasattr(constants, "ADMIN_ROLE_NAMES")
    assert "Админ" in constants.ADMIN_ROLE_NAMES
    assert "Admin" in constants.ADMIN_ROLE_NAMES
    assert "admin" in constants.ADMIN_ROLE_NAMES


def test_inventory_system_uses_logistics_tag_constant():
    """InventorySystem must reference LOGISTICS_REQUEST_TAG from constants, not a literal."""
    import inspect

    import docuflow.features.inventory.system as mod

    source = inspect.getsource(mod)
    assert '"[LOGISTICS_REQUEST]"' not in source, (
        "inventory/system.py must use constants.LOGISTICS_REQUEST_TAG, not the literal"
    )
    assert "'[LOGISTICS_REQUEST]'" not in source
