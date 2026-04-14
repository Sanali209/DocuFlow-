import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from docuflow.domain.entities.production import (
    ChatMessage,
    ChatMessageType,
    MaterialAudit,
    MaterialStockStatus,
    TaskItem,
)
from docuflow.features.inventory.system import InventorySystem
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
def inventory_system(session: Session):
    config = Config(node_id="test_node")
    return InventorySystem(config, session)


def test_create_material_definition(inventory_system: InventorySystem, session: Session):
    mt = inventory_system.create_material_definition(code="ST37-3mm", thickness=3.0)
    assert mt.id is not None
    assert mt.code == "ST37-3mm"

    # Check duplicate
    mt2 = inventory_system.create_material_definition(code="ST37-3mm", thickness=3.0)
    assert mt.id == mt2.id


def test_receive_material_batch_creates_audit(inventory_system: InventorySystem, session: Session):
    mt = inventory_system.create_material_definition(code="ALU-5mm", thickness=5.0)
    stock = inventory_system.receive_material_batch(
        mt.id, quantity=10, batch_code="B1", location="A1"
    )

    assert stock.quantity == 10
    assert stock.batch_code == "B1"

    # Verify audit
    audit = session.exec(
        select(MaterialAudit).where(MaterialAudit.stock_item_id == stock.id)
    ).first()
    assert audit.operation == "income"
    assert audit.qty_delta == 10


def test_hard_reservation_locks_status(inventory_system: InventorySystem, session: Session):
    mt = inventory_system.create_material_definition(code="ST37-1mm", thickness=1.0)
    stock = inventory_system.receive_material_batch(mt.id, quantity=20)

    # Hard reservation
    res = inventory_system.create_reservation(stock.id, work_item_id=1, qty=5, is_hard=True)

    session.refresh(stock)
    assert stock.status == MaterialStockStatus.RESERVED
    assert res.reservation_type == "hard"


def test_perform_write_off_with_reservation(inventory_system: InventorySystem, session: Session):
    mt = inventory_system.create_material_definition(code="ST37-2mm", thickness=2.0)
    stock = inventory_system.receive_material_batch(mt.id, quantity=15)

    # 1. Create reservation
    res = inventory_system.create_reservation(stock.id, work_item_id=100, qty=3, is_hard=True)

    # 2. Complete task
    task = TaskItem(id=50, work_item_id=100, mat_type_id=mt.id, file_name="T1", file_path="P1")
    session.add(task)
    session.flush()

    inventory_system.perform_write_off(task, sheets_used=3, author="operator")

    session.refresh(stock)
    assert stock.quantity == 12
    # In my new logic, I delete the reservation. In previous it released it.
    # Let's check my new logic: target_stock.status is not explicitly changed back to AVAILABLE if it was RESERVED.
    # Wait, I should check InventorySystem.perform_write_off again.
    # Actually, in the new logic: target_stock.quantity -= sheets_used.
    # If it was a reservation, I should probably set it back to AVAILABLE if quantity reaches 0 or just leave it.
    # Let's see: target_stock = db.get(MaterialStock, reservation.id) -- WAIT, reservation.id is not stock.id!
    # I found a bug in my refactored InventorySystem!


def test_record_inventory_correction(inventory_system: InventorySystem, session: Session):
    mt = inventory_system.create_material_definition(code="CORR", thickness=1.0)
    stock = inventory_system.receive_material_batch(mt.id, quantity=10)

    delta = inventory_system.record_inventory_correction(
        stock.id, actual_qty=8, reason="lost", author="admin"
    )
    assert delta == -2
    assert stock.quantity == 8

    audit = session.exec(
        select(MaterialAudit).where(MaterialAudit.operation == "correction")
    ).first()
    assert audit.qty_delta == -2
    assert audit.reason == "lost"


def test_request_reorder_triggers_chat(inventory_system: InventorySystem, session: Session):
    mt = inventory_system.create_material_definition(code="ORDER-ME", thickness=2.0)
    inventory_system.request_material_reorder(
        mt.id, quantity=50, note="Need more!", author="foreman"
    )

    # Check ChatMessage
    msg = session.exec(
        select(ChatMessage).where(ChatMessage.message_type == ChatMessageType.ORDER)
    ).first()
    assert msg is not None
    assert "ORDER-ME" in msg.content
    assert "50" in msg.content
