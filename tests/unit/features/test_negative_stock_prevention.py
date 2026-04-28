import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    MaterialStock,
    MaterialStockStatus,
    MaterialType,
    TaskItem,
)
from docuflow.features.inventory.system import InventorySystem
from docuflow.infrastructure.config import Config


def test_negative_stock_prevention():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 1. Setup Stock (5 sheets)
        mat = MaterialType(code="TEST-MAT", thickness=1.0)
        session.add(mat)
        session.commit()
        session.refresh(mat)

        stock = MaterialStock(
            mat_type_id=mat.id,
            quantity=5,
            status=MaterialStockStatus.AVAILABLE,
            batch_code="BATCH-001",
        )
        session.add(stock)
        session.commit()

        # 2. Setup Task requesting 10 sheets
        task = TaskItem(
            work_item_id=1, file_name="part.gnc", file_path="/p", mat_type_id=mat.id, sheet_qty=10
        )
        session.add(task)
        session.commit()

        inv_sys = InventorySystem(Config(), session)

        # 3. Attempt write-off of 10 sheets
        with pytest.raises(ValueError) as excinfo:
            inv_sys.perform_write_off(task, sheets_used=10, author="operator")

        assert "Недостаточно материала" in str(excinfo.value)

        # 4. Verify stock remains unchanged
        session.refresh(stock)
        assert stock.quantity == 5
