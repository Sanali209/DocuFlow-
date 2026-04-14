import pytest
from sqlmodel import Session, SQLModel, create_engine

from docuflow.features.inventory.system import InventorySystem
from docuflow.infrastructure.config import Config


@pytest.fixture(name="config")
def config_fixture():
    return Config(node_id="TEST_NODE")


@pytest.fixture(name="session")
def session_fixture():
    """Providing an in-memory SQLModel session for isolated inventory testing."""
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_material_creation(session, config):
    """Verifying that new materials are correctly persisted."""
    inventory = InventorySystem(config, session)

    # Create material
    material = inventory.create_material_definition(code="Steel Sheet", thickness=2.0)

    assert material.id is not None
    assert material.code == "Steel Sheet"


def test_absolute_stock_update(session, config):
    """Confirming that stock levels can be adjusted."""
    inventory = InventorySystem(config, session)

    # Pre-create material type and stock
    mt = inventory.create_material_definition(code="Aluminum", thickness=3.0)
    batch = inventory.receive_material_batch(mat_type_id=mt.id, quantity=10.0, batch_code="B1")

    # Perform correction
    inventory.record_inventory_correction(
        batch.id, actual_qty=25.0, reason="Found more", author="test"
    )

    session.refresh(batch)
    assert batch.quantity == 25.0
