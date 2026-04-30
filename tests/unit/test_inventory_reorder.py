import pytest
from sqlalchemy import event as sa_event
from sqlmodel import Session, SQLModel, create_engine

from docuflow.features.inventory.system import InventorySystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def inventory_system(tmp_path):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @sa_event.listens_for(engine, "connect")
    def set_pragma(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    config = Config(node_id="TEST", shared_path=str(tmp_path))
    session = Session(engine)
    return InventorySystem(config, session)


def test_request_material_reorder_no_fk_violation(inventory_system):
    """request_material_reorder must not create MaterialAudit(stock_item_id=0)."""
    from docuflow.domain.entities.production import MaterialType

    # Create a material type
    mat = MaterialType(code="ALU-3", thickness=3.0)
    inventory_system.db_session.add(mat)
    inventory_system.db_session.flush()
    inventory_system.db_session.refresh(mat)

    # Must not raise IntegrityError
    inventory_system.request_material_reorder(
        mat_type_id=mat.id,
        quantity=100,
        note="Low stock",
        author="test_user",
    )
    inventory_system.db_session.commit()

    # Verify no MaterialAudit with stock_item_id=0 was created
    from docuflow.domain.entities.production import MaterialAudit
    from sqlmodel import select

    bad_audits = list(
        inventory_system.db_session.exec(
            select(MaterialAudit).where(MaterialAudit.stock_item_id == 0)
        ).all()
    )
    assert len(bad_audits) == 0, "No MaterialAudit with stock_item_id=0 should exist"
