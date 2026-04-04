import pytest
from unittest.mock import MagicMock
from sqlmodel import Session, create_engine, SQLModel
from docuflow.application.inventory import InventorySystem
from docuflow.domain.entities.production import MaterialStock
from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.infrastructure.security import HMACSigner

@pytest.fixture(name="session")
def session_fixture():
    """Providing an in-memory SQLModel session for isolated inventory testing."""
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="signer")
def hmac_signer_fixture():
    """Providing a mock HMAC signer for cryptographic identity testing."""
    return HMACSigner("test_secret")

@pytest.fixture(name="orchestrator")
def orchestrator_mock():
    """Providing a mocked P2P orchestrator to capture synchronization commands."""
    return MagicMock(spec=P2POrchestrator)

def test_material_creation(session, orchestrator, signer):
    """Verifying that new materials are correctly persisted and broadcasted."""
    inventory = InventorySystem(session, orchestrator, signer)
    
    # Create material
    material = inventory.create_material("Steel Sheet", 50.0, "pcs")
    
    assert material.id is not None
    assert material.name == "Steel Sheet"
    
    # Verify P2P broadcast
    orchestrator.broadcast_command.assert_called_once()
    args, kwargs = orchestrator.broadcast_command.call_args
    assert kwargs["command"] == "CREATE_MATERIAL"
    assert kwargs["data"]["name"] == "Steel Sheet"

def test_absolute_stock_update(session, orchestrator, signer):
    """Confirming that stock updates follow the absolute-value sync model."""
    inventory = InventorySystem(session, orchestrator, signer)
    
    # Pre-create material
    m = MaterialStock(name="Aluminum", quantity=10.0, unit="kg")
    session.add(m)
    session.commit()
    session.refresh(m)
    
    # Perform absolute update
    updated = inventory.update_stock(m.id, 25.0)
    
    assert updated.quantity == 25.0
    
    # Verify P2P synchronization
    orchestrator.broadcast_command.assert_called_once()
    args, kwargs = orchestrator.broadcast_command.call_args
    assert kwargs["command"] == "UPDATE_STOCK"
    assert kwargs["data"]["quantity"] == 25.0
