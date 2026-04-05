import pytest
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import (
    MaterialType,
    ProductionUnit,
    TaskItem,
    TaskPart,
    WorkItem,
    WorkItemType,
)
from docuflow.features.parts.system import PartLibrarySystem
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
def parts_system(session: Session):
    config = Config(node_id="test_node")
    return PartLibrarySystem(config, db_session=session)


def test_upsert_part_idempotency(parts_system: PartLibrarySystem, session: Session):
    # 1. First creation
    part = parts_system.synchronize_part_definition(sku="SKU-01", bbox_x=100.0, bbox_y=50.0)
    assert part.sku == "SKU-01"
    assert part.bbox_x == 100.0
    first_seen = part.first_seen_at

    # 2. Second call with updated metadata
    part2 = parts_system.synchronize_part_definition(sku="SKU-01", bbox_x=105.0)
    assert part2.id == part.id
    assert part2.bbox_x == 105.0
    assert part2.first_seen_at == first_seen  # Preserved


def test_find_by_bbox_tolerance(parts_system: PartLibrarySystem, session: Session):
    parts_system.synchronize_part_definition(sku="PART-A", bbox_x=100.0, bbox_y=100.0)
    parts_system.synchronize_part_definition(sku="PART-B", bbox_x=104.0, bbox_y=104.0)  # Within 5%
    parts_system.synchronize_part_definition(sku="PART-C", bbox_x=110.0, bbox_y=110.0)  # Outside 5%

    results = parts_system.find_parts_by_geometric_similarity(100.0, 100.0, tolerance_percent=5.0)
    skus = [p.sku for p in results]
    assert "PART-A" in skus
    assert "PART-B" in skus
    assert "PART-C" not in skus


def test_inverse_traceability(parts_system: PartLibrarySystem, session: Session):
    # Setup: Part -> TaskPart -> TaskItem -> WorkItem
    part = parts_system.synchronize_part_definition(sku="TRACEME")

    mt = MaterialType(code="TEST-MAT", thickness=1.0)
    session.add(mt)
    session.flush()

    from docuflow.domain.entities.production import Project

    proj = Project(name="PROJ-1")
    session.add(proj)
    session.flush()

    wi = WorkItem(
        folder_name="PROJECT-X",
        folder_path="path/to/x",
        sidra_number="S-123",
        project_id=proj.id,
        work_item_type=WorkItemType.SIDRA,
    )
    session.add(wi)
    session.flush()

    ti = TaskItem(work_item_id=wi.id, mat_type_id=mt.id, file_name="part.gnc", file_path="path")
    session.add(ti)
    session.flush()

    tp = TaskPart(task_item_id=ti.id, part_sku="TRACEME", qty=5)
    session.add(tp)
    session.flush()

    # Check WorkItems
    work_items = parts_system.trace_work_items_for_sku("TRACEME")
    assert len(work_items) == 1
    assert work_items[0].folder_name == "PROJECT-X"

    # Setup: TaskItem -> ProductionUnit
    pu = ProductionUnit(task_item_id=ti.id, qty_produced=10, label_id="L-001", created_by="worker")
    session.add(pu)
    session.flush()

    # Check Pallets
    pallets = parts_system.trace_pallets_for_sku("TRACEME")
    assert len(pallets) == 1
    assert pallets[0].label_id == "L-001"


def test_part_templates_crud(parts_system: PartLibrarySystem, session: Session):
    parts_system.create_part_template(
        sku="SKU-T", note_message="Dangerous corner", severity_level="critical"
    )
    parts_system.create_part_template(sku="SKU-T", note_message="Info only", severity_level="info")

    templates = parts_system.list_part_templates("SKU-T")
    assert len(templates) == 2
    assert any(t.severity == "critical" for t in templates)

    # Delete
    parts_system.remove_part_template(templates[0].id)
    assert len(parts_system.list_part_templates("SKU-T")) == 1
