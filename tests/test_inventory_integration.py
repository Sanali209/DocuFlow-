from docuflow.domain.settings import registry


def test_inventory_settings_registration():
    """Verify that the Inventory module correctly registers its expanded declarative schema."""
    from docuflow.features.inventory.system import InventorySettings

    schema = registry.get_schema("inventory")
    assert schema is not None, "Inventory schema should be registered"
    assert schema == InventorySettings

    # Verify Global Fields
    globals = registry.get_fields_by_scope("inventory", "global")
    assert "warehouse_display_name" in globals
    assert "enable_p2p_sync" in globals
    assert "poll_interval_seconds" not in globals

    # Verify Local Fields
    locals = registry.get_fields_by_scope("inventory", "local")
    assert "poll_interval_seconds" in locals
    assert "low_stock_threshold" in locals
    assert "warehouse_display_name" not in locals
