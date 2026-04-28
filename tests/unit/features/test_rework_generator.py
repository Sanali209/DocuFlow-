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
    part = PartLibrary(sku="BASE-001", mat_type_id=mat.id, bbox_x=100, bbox_y=50)
    session.add(part)
    session.commit()

    gen = ReworkGenerator(session, shared_path="/tmp")
    result = gen.generate("REWORK-001", project.id, [CartItem(sku="BASE-001", qty=4)])

    assert result.folder_name == "REWORK-001"
