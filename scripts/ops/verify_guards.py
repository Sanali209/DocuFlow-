import asyncio

from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import TaskItem, TaskItemStatus
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.infrastructure.config import Config


async def verify_guard_clauses():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Test TaskBoardSystem Guard
        print("Test 1: Production Volume Validation...")
        sys = TaskBoardSystem(Config(), engine)
        t3 = TaskItem(
            work_item_id=1,
            file_name="T3",
            file_path="/p3",
            sheet_qty=10,
            status=TaskItemStatus.IN_PROGRESS,
        )
        session.add(t3)
        session.commit()

        try:
            sys.complete_task(t3.id, sheets_done=100, qty_produced=50)
            print("❌ FAIL: System allowed excessive sheet count!")
        except ValueError as e:
            print(f"✅ SUCCESS: {e}")


if __name__ == "__main__":
    asyncio.run(verify_guard_clauses())
