import asyncio

from sqlmodel import Session, SQLModel, create_engine, select

from docuflow.domain.entities.production import (
    MaterialType,
    TaskItem,
    TaskItemStatus,
    WorkerBucketEntry,
    WorkItem,
    WorkLog,
)
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.infrastructure.config import Config


async def run_operator_simulation():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    config = Config()
    config.node_id = "LASER_1"

    with Session(engine) as session:
        # 1. Setup Environment
        mat = MaterialType(code="09Г2С 10mm", thickness=10.0)
        session.add(mat)
        session.commit()

        wi = WorkItem(folder_name="SIM-PROJECT", folder_path="/sim", project_id=1)
        session.add(wi)
        session.commit()

        task = TaskItem(
            work_item_id=wi.id,
            file_name="GNC-SIM-01.gnc",
            file_path="/sim/gnc",
            sheet_qty=5,
            mat_type_id=mat.id,
            status=TaskItemStatus.PLANNED,
        )
        session.add(task)
        session.commit()

        # Assign to node
        bucket = WorkerBucketEntry(
            node_id="LASER_1", assigned_user="sim_operator", task_item_id=task.id
        )
        session.add(bucket)
        session.commit()

        # 2. Simulate Operator Actions via System
        sys = TaskBoardSystem(config, engine)

        print("--- SIMULATION START ---")

        # Start Task
        sys.start_task(task.id)
        print("Action: Started Task")

        # Pause with Incident
        sys.report_material_incident(task.id, "Sheet deformation detected")
        sys.pause_task(task.id, "Waiting for new sheet")
        print("Action: Paused Task + Reported Incident")

        # 3. Verification
        with Session(engine) as check_session:
            # Check Logs
            logs = check_session.exec(select(WorkLog).order_by(WorkLog.created_at.desc())).all()
            print("\nAudit Log Verification:")
            for l in logs:
                print(f"[{l.created_at.strftime('%H:%M:%S')}] {l.message}")

            # Check Task Status
            updated_task = check_session.get(TaskItem, task.id)
            print(f"\nFinal Task Status: {updated_task.status}")

            # Check for logistics signal (INCIDENT in logs)
            incident_logs = [l for l in logs if "[MATERIAL_INCIDENT]" in l.message]
            if incident_logs:
                print("\n✅ SUCCESS: Material incident signal captured for warehouse!")


if __name__ == "__main__":
    asyncio.run(run_operator_simulation())
