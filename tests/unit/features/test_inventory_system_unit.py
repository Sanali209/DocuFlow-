import pytest

pytest.skip(
    "Duplicate inventory test in application; skipping unit duplicate.", allow_module_level=True
)
from unittest.mock import AsyncMock, MagicMock

from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    MaterialAudit,
    MaterialStock,
    MaterialType,
    TaskItem,
    TaskItemStatus,
    WorkItem,
)
from docuflow.features.inventory.system import InventorySystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="mock_sdk")
def mock_sdk_fixture():
    """Создаёт мок SDK."""
    sdk = MagicMock()
    sdk.resolve_system_by_type = AsyncMock()
    sdk.orchestrator = None  # Default
    return sdk


@pytest.fixture(name="config")
def config_fixture():
    """Создаёт тестовую конфигурацию."""
    return Config(node_id="test_node")


@pytest.fixture(name="session")
def session_fixture(engine):
    """Создаёт сессию для тестов."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="inventory_system")
def inventory_system_fixture(config: Config, session: Session, mock_sdk):
    """Создаёт экземпляр InventorySystem."""
    return InventorySystem(config=config, db_session=session, sdk=mock_sdk)


def test_seed_and_get_material_catalog(inventory_system, session):
    """Тест получения каталога материалов."""
    mt = MaterialType(code="ST3-2mm", thickness=2.0)
    session.add(mt)
    session.flush()

    catalog = inventory_system.get_material_catalog()
    assert len(catalog) >= 1
    assert catalog[0].code == "ST3-2mm"


def test_perform_write_off_handles_negative_stock(inventory_system, session, mock_sdk):
    """Тест списания материала (допускается отрицательный остаток)."""
    # Setup
    mt = MaterialType(code="ALU-3mm", thickness=3.0)
    session.add(mt)
    session.flush()
    session.refresh(mt)

    stock = MaterialStock(mat_type_id=mt.id, quantity=5.0, location="A1")
    session.add(stock)

    wi = WorkItem(
        folder_name="TEST",
        folder_path="path",
        project_id=1,
        sidra_number="S-1",
        work_item_type="laser",
    )
    session.add(wi)
    session.flush()
    session.refresh(wi)

    task = TaskItem(
        work_item_id=wi.id,
        file_name="part.gnc",
        file_path="path",
        status=TaskItemStatus.PLANNED,
        mat_type_id=mt.id,
    )
    session.add(task)
    session.flush()
    session.refresh(task)

    # Execute
    inventory_system.perform_write_off(task, sheets_used=10, author="operator")

    # Verify
    session.refresh(stock)
    assert stock.quantity == -5.0

    audit = session.exec(
        select(MaterialAudit).where(MaterialAudit.ref_task_item_id == task.id)
    ).first()
    assert audit is not None
    assert audit.qty_delta == -10.0

    # Verify Notification was emitted (async call in sync method? I might need to handle this)
    # ns.emit.assert_called_with("inventory.stock_low", ...)
