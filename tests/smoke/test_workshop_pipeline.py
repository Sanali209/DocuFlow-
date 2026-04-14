import pytest

pytest.importorskip("passlib")
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import MaterialType, TaskItem, WorkItemType
from docuflow.features.auth.system import AuthSystem
from docuflow.features.projects.system import ProjectSystem
from docuflow.features.reports.system import ReportRegistry, ReportSystem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.work_items.system import WorkItemSystem
from docuflow.infrastructure.config import Config


@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="config")
def config_fixture():
    return Config(node_id="smoke_node")


@pytest.mark.asyncio
async def test_full_workshop_pipeline(db_session: Session, config: Config):
    """
    Smoke test for the entire refactored workshop pipeline.

    Verifies:
    1. AuthSystem bootstrap
    2. ProjectSystem resolution
    3. WorkItemSystem ingestion
    4. TaskBoardSystem lifecycle
    5. ReportSystem rendering
    """
    # 1. Identity & Projects
    auth = AuthSystem(config, db_session)
    admin = auth.bootstrap_admin()
    assert admin is not None

    project_sys = ProjectSystem(config, db_session)
    default_project = project_sys.resolve_default_workshop_project()
    assert default_project.name == "Default"

    # 2. Ingestion
    work_item_sys = WorkItemSystem(config, db_session)
    work_item = work_item_sys.create_work_item(
        folder_name="SMOKE-BATCH-001", folder_path="/workshop/smoke", item_type=WorkItemType.SIDRA
    )
    assert work_item.id is not None

    # 3. Production Planning
    material = MaterialType(code="ST37", thickness=3.0)
    db_session.add(material)
    db_session.commit()

    task_item = TaskItem(
        file_name="part1.gnc",
        file_path="smoke/part1.gnc",
        work_item_id=work_item.id,
        mat_type_id=material.id,
        batch_group_id="BATCH-01",
        estimated_minutes=10,
    )
    db_session.add(task_item)
    db_session.commit()

    # 4. Workshop Operations
    task_board = TaskBoardSystem(config, db_session)

    # Lock for operator
    entries = await task_board.lock_batch("BATCH-01", "NODE-1", "operator1")
    assert len(entries) == 1

    # Lifecycle
    task_board.start_task(task_item.id)
    task_board.complete_task(task_item.id, sheets_done=1, qty_produced=10)

    db_session.refresh(work_item)
    from docuflow.domain.entities.production import WorkItemStatus

    assert work_item.status == WorkItemStatus.DONE

    # 5. Reporting
    from docuflow.features.reports.system import ReportDataBlock

    registry = ReportRegistry()

    # Mock some blocks for the shift summary
    registry.register(
        ReportDataBlock(
            name="downtime_summary",
            label="Downtime",
            params=[],
            query_fn=lambda s, p: {"Mechanical": 10.5, "Electrical": 5.0},
        )
    )
    registry.register(
        ReportDataBlock(name="incident_log", label="Incidents", params=[], query_fn=lambda s, p: [])
    )

    report_sys = ReportSystem(config, db_session, registry)
    await report_sys.on_startup()  # Seed default templates

    html_preview = report_sys.generate_html_preview(
        report_sys.TEMPLATE_SHIFT_SUMMARY, {"date_from": "2024-01-01", "date_to": "2024-12-31"}
    )
    assert "SHIFT PERFORMANCE" in html_preview
    assert "Mechanical" in html_preview
