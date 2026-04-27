import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import (
    MaterialType,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
    WorkItem,
)
from docuflow.features.task_board.task_group_service import TaskGroupService


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


def test_auto_group_by_material(session):
    # Setup
    mat = MaterialType(code="ST37-2", thickness=4.0)
    session.add(mat)
    session.flush()

    wi = WorkItem(project_id=1, folder_name="test", folder_path="test")
    session.add(wi)
    session.flush()

    t1 = TaskItem(
        work_item_id=wi.id,
        file_name="a.gnc",
        file_path="a.gnc",
        mat_type_id=mat.id,
        thickness=4.0,
        status=TaskItemStatus.PLANNED,
    )
    t2 = TaskItem(
        work_item_id=wi.id,
        file_name="b.gnc",
        file_path="b.gnc",
        mat_type_id=mat.id,
        thickness=4.0,
        status=TaskItemStatus.PLANNED,
    )
    session.add_all([t1, t2])
    session.commit()

    service = TaskGroupService(session)
    groups = service.auto_group_by_material(wi.id)

    assert len(groups) == 1
    assert groups[0].name == "ST37-2 4.0mm"
    assert len(groups[0].tasks) == 2
