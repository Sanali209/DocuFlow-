import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import MaterialType, PartLibrary, Project
from docuflow.features.parts.order_cart import CartItem
from docuflow.features.parts.rework_generator import ReworkGenerator


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_generate_rework_work_item(session):
    project = Project(name="Test")
    session.add(project)
    mat = MaterialType(code="ST37-2", thickness=4.0)
    session.add(mat)
    session.commit()
    part = PartLibrary(sku="BASE-001", mat_type_id=mat.id, bbox_x=100, bbox_y=50)
    session.add(part)
    session.commit()

    gen = ReworkGenerator(session, shared_path="/tmp")  # noqa: S108
    result = gen.generate("REWORK-001", project.id, [CartItem(sku="BASE-001", qty=4)])

    assert result.folder_name == "REWORK-001"


def test_generate_creates_gnc_files(session, tmp_path):
    project = Project(name="Test")
    session.add(project)
    mat = MaterialType(code="ST37-2", thickness=4.0)
    session.add(mat)
    session.commit()
    part = PartLibrary(sku="BASE-001", mat_type_id=mat.id, bbox_x=100, bbox_y=50)
    session.add(part)
    session.commit()

    gen = ReworkGenerator(session, shared_path=str(tmp_path))
    _result = gen.generate("REWORK-001", project.id, [CartItem(sku="BASE-001", qty=2)])

    gnc_file = tmp_path / "rework/REWORK-001/Sheet_ST37-2_4.0.GNC"
    assert gnc_file.exists()
    content = gnc_file.read_text()
    assert "(*SHEET" in content
    assert "(PART NAME: BASE-001)" in content
    assert "G01" in content
