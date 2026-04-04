import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from docuflow.features.consumables.system import ConsumableSystem
from docuflow.domain.entities.production import (
    Consumable, 
    ConsumableLog, 
    ChatMessage, 
    ChatMessageType
)
from docuflow.infrastructure.config import Config

@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture
def consumable_system(session: Session):
    config = Config(node_id="test_node")
    return ConsumableSystem(config, db_session=session)

def test_create_consumable(consumable_system: ConsumableSystem, session: Session):
    item = consumable_system.create_consumable("Nozzle 1.5", category="nozzle", min_quantity=10.0)
    assert item.id is not None
    assert item.name == "Nozzle 1.5"
    assert item.quantity == 0.0

def test_use_reduces_quantity_and_logs(consumable_system: ConsumableSystem, session: Session):
    item = consumable_system.create_consumable("Tape", min_quantity=1.0)
    consumable_system.restock(item.id, quantity_delta=10.0, author="admin")
    
    consumable_system.use_consumable(item.id, quantity_used=3.0, author="worker", note="Job A")
    
    session.refresh(item)
    assert item.quantity == 7.0
    
    logs = consumable_system.get_movement_history(item.id)
    assert len(logs) == 2 # restock + use
    assert logs[0].operation == "use"
    assert logs[0].qty_delta == -3.0

def test_critical_alert_triggers_chat(consumable_system: ConsumableSystem, session: Session):
    item = consumable_system.create_consumable("Lens", min_quantity=5.0)
    consumable_system.restock(item.id, quantity_delta=6.0)
    
    # Use 2 -> quantity becomes 4 (below min 5)
    consumable_system.use_consumable(item.id, quantity_used=2.0)
    
    # Check for ChatMessage
    stmt = select(ChatMessage).where(ChatMessage.message_type == ChatMessageType.WARNING)
    msg = session.exec(stmt).first()
    assert msg is not None
    assert "КРИТИЧЕСКИЙ ОСТАТОК" in msg.content
    assert "Lens" in msg.content

def test_list_critical_filter(consumable_system: ConsumableSystem, session: Session):
    consumable_system.create_consumable("OK", min_quantity=5.0)
    consumable_system.restock(consumable_system.get_consumable_by_name("OK").id, quantity_delta=10.0)
    
    consumable_system.create_consumable("CRITICAL", min_quantity=5.0)
    consumable_system.restock(consumable_system.get_consumable_by_name("CRITICAL").id, quantity_delta=2.0)
    
    critical_list = consumable_system.list_consumables(with_critical=True)
    assert len(critical_list) == 1
    assert critical_list[0].name == "CRITICAL"

def test_write_off(consumable_system: ConsumableSystem, session: Session):
    item = consumable_system.create_consumable("Glass", min_quantity=0.0)
    consumable_system.restock(item.id, quantity_delta=5.0)
    
    consumable_system.perform_write_off(item.id, quantity_lost=1.0, reason="Broken", author="admin")
    
    session.refresh(item)
    assert item.quantity == 4.0
    
    log = consumable_system.get_movement_history(item.id)[0]
    assert log.operation == "write_off"
    assert log.note == "Broken"
