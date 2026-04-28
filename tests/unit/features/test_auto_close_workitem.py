import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import TaskItem, TaskItemStatus, WorkItem, WorkItemStatus
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.infrastructure.config import Config


@pytest.mark.asyncio
async def test_auto_close_work_item():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create a work item with 2 tasks
        wi = WorkItem(
            folder_name="PROJECT-AUTO-CLOSE",
            folder_path="/test",
            project_id=1,
            status=WorkItemStatus.IN_PROGRESS,
        )
        session.add(wi)
        session.commit()
        session.refresh(wi)

        t1 = TaskItem(
            work_item_id=wi.id,
            file_name="part1.gnc",
            file_path="/test/1",
            sheet_qty=1,
            status=TaskItemStatus.PLANNED,
        )
        t2 = TaskItem(
            work_item_id=wi.id,
            file_name="part2.gnc",
            file_path="/test/2",
            sheet_qty=1,
            status=TaskItemStatus.PLANNED,
        )
        session.add(t1)
        session.add(t2)
        session.commit()

        task_sys = TaskBoardSystem(Config(), engine, session)

        # Start tasks first (required transition)
        task_sys.start_task(t1.id)
        task_sys.start_task(t2.id)
        session.commit()

        # 1. Complete first task
        task_sys.complete_task(t1.id, sheets_done=1, qty_produced=10)
        session.commit()  # Commit in test as session is injected

        session.refresh(wi)
        # Should still be IN_PROGRESS
        assert wi.status == WorkItemStatus.IN_PROGRESS

        # 2. Complete second task
        task_sys.complete_task(t2.id, sheets_done=1, qty_produced=10)
        session.commit()  # Commit in test

        session.refresh(wi)
        # NOW it should be DONE automatically
        assert wi.status == WorkItemStatus.DONE
        assert wi.completed_at is not None
