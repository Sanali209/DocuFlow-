import pytest
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import TaskItem, WorkItem, WorkLog
from docuflow.features.core.search import SearchSystem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.work_items.system import WorkItemFilters, WorkItemSystem
from docuflow.infrastructure.config import Config


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.mark.asyncio
async def test_search_system_integration(test_db):
    with Session(test_db) as session:
        # Seed
        wi = WorkItem(
            folder_name="PROJECT-X-123",
            folder_path="C:/test/path",
            sidra_number="SID-001",
            project_id=1,
        )
        session.add(wi)
        session.commit()

        search_sys = SearchSystem(session)

        # Test finding work item
        results = await search_sys.search("PROJECT")
        assert len(results) >= 1
        assert results[0].title == "PROJECT-X-123"
        assert results[0].view_name == "work_items"


@pytest.mark.asyncio
async def test_material_incident_logging(test_db):
    with Session(test_db) as session:
        # Seed
        wi = WorkItem(folder_name="Test", folder_path="C:/test/path", project_id=1)
        session.add(wi)
        session.commit()

        task = TaskItem(
            work_item_id=wi.id,
            file_name="part.gnc",
            file_path="C:/test/path/part.gnc",
            sheet_qty=10,
        )
        session.add(task)
        session.commit()

        config = Config()
        # TaskBoardSystem requires db_engine and optionally session
        task_sys = TaskBoardSystem(config, db_engine=test_db, session=session)

        # Trigger incident
        task_sys.report_material_incident(task.id, "Defect found")

        # Verify log exists
        from sqlmodel import select

        logs = session.exec(
            select(WorkLog).where(WorkLog.message.contains("[MATERIAL_INCIDENT]"))
        ).all()
        assert len(logs) == 1
        assert "Defect found" in logs[0].message


@pytest.mark.asyncio
async def test_work_item_filters_logic(test_db):
    with Session(test_db) as session:
        # Seed
        wi1 = WorkItem(folder_name="ALPHA", folder_path="C:/path1", project_id=1)
        wi2 = WorkItem(folder_name="BETA", folder_path="C:/path2", project_id=1)
        session.add(wi1)
        session.add(wi2)
        session.commit()

        wi_sys = WorkItemSystem(Config(), session, None)

        # Test Filter by text
        filters = WorkItemFilters(search_text="ALPHA")
        results = wi_sys.list_work_items_by_filter(filters)
        assert len(results) == 1
        assert results[0].folder_name == "ALPHA"
