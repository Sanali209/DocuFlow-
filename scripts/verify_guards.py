import asyncio

from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import MaterialType, TaskItem, TaskItemStatus
from docuflow.features.task_board.batch_engine import BatchEngine
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.infrastructure.config import Config


async def verify_guard_clauses():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Setup
        m1 = MaterialType(code="MAT1", thickness=1.0)
        m2 = MaterialType(code="MAT2", thickness=2.0)
        session.add(m1)
        session.add(m2)
        session.commit()

        t1 = TaskItem(
            work_item_id=1, file_name="T1", file_path="/p1", mat_type_id=m1.id, thickness=1.0
        )
        t2 = TaskItem(
            work_item_id=1, file_name="T2", file_path="/p2", mat_type_id=m2.id, thickness=2.0
        )
        session.add(t1)
        session.add(t2)
        session.commit()

        # 1. Test BatchEngine Guard
        print("Test 1: BatchEngine Material Validation...")
        engine_logic = BatchEngine(session)
        try:
            engine_logic.create_batch([t1.id, t2.id])
            print("❌ FAIL: BatchEngine allowed different materials!")
        except ValueError as e:
            print(f"✅ SUCCESS: {e}")

        # 2. Test TaskBoardSystem Guard
        print("\nTest 2: Production Volume Validation...")
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
