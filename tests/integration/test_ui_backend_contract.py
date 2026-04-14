import pytest
from sqlmodel import Session, create_engine

from docuflow.features.task_board.batch_engine import BatchEngine
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.work_items.system import WorkItemSystem
from docuflow.infrastructure.config import Config


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    with Session(engine) as session:
        yield session


@pytest.fixture(name="config")
def config_fixture():
    return Config(node_id="test_node")


class TestUIBackendContract:
    """
    Интеграционный тест-контракт.
    Проверяет, что бэкенд-системы реализуют все методы, которые вызываются в UI-виджетах.
    Это предотвращает ошибки AttributeError в рантайме NiceGUI.
    """

    def test_work_item_system_contract(self, config, session):
        """Проверка контракта WorkItemSystem (используется в WorkItemCard)."""
        system = WorkItemSystem(config=config, session=session)

        assert hasattr(system, "register_document"), (
            "WorkItemSystem должен иметь метод register_document"
        )
        assert hasattr(system, "update_status"), "WorkItemSystem должен иметь метод update_status"

    def test_task_board_system_contract(self, config, session):
        """Проверка контракта TaskBoardSystem (используется в BucketPanel, BatchCard, Dialogs)."""
        # TaskBoardSystem requires db_engine and optionally session
        engine = session.get_bind()
        system = TaskBoardSystem(config=config, db_engine=engine, session=session)

        expected_methods = [
            "get_bucket",
            "start_task",
            "pause_task",
            "resume_task",
            "complete_task",
            "block_task",
            "assign_task_to_node",
            "get_matching_unassigned_tasks",
            "report_material_incident",
        ]

        for method in expected_methods:
            assert hasattr(system, method), f"TaskBoardSystem должен иметь метод {method}"

    def test_batch_engine_contract(self, session):
        """Проверка контракта BatchEngine (используется в BatchCard)."""
        engine = BatchEngine(session=session)

        assert hasattr(engine, "check_stock_alerts"), (
            "BatchEngine должен иметь метод check_stock_alerts"
        )
