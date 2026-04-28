"""
Тесты для TaskBoardSystem.

TDD подход:
1. Сначала тесты
2. Потом код
3. Рефакторинг
"""

from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    MaterialType,
    Project,
    TaskGroup,
    TaskItem,
    TaskItemStatus,
    TaskPart,
    WorkItem,
)
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.infrastructure.config import Config


@pytest.fixture(name="engine")
def engine_fixture():
    """Создаёт in-memory SQLite engine для тестов."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """Создаёт in-memory SQLite сессию для тестов."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="config")
def config_fixture():
    """Создаёт тестовую конфигурацию."""
    return Config(node_id="test_node", shared_path="./test_shared")


@pytest.fixture(name="system")
def system_fixture(config: Config, session: Session, engine):
    """Creates a TaskBoardSystem instance."""
    from unittest.mock import MagicMock

    inv = MagicMock()
    prod = MagicMock()
    ns = MagicMock()
    return TaskBoardSystem(
        config=config,
        db_engine=engine,
        session=session,
        inventory_system=inv,
        production_system=prod,
        ns_mirror=ns,
    )


@pytest.fixture(name="project_and_work_item")
def project_and_work_item_fixture(session: Session):
    """Создаёт проект и WorkItem."""
    project = Project(name="Test")
    session.add(project)
    session.commit()

    work_item = WorkItem(
        folder_name="test",
        folder_path="/test",
        project_id=project.id,
    )
    session.add(work_item)
    session.commit()
    session.refresh(work_item)

    return project, work_item


@pytest.fixture(name="material")
def material_fixture(session: Session):
    """Создаёт тестовый материал."""
    mat = MaterialType(code="ST37", thickness=3.0, nominal_x=3000, nominal_y=1500)
    session.add(mat)
    session.commit()
    session.refresh(mat)
    return mat


class TestTaskBoardSystemAssignTaskGroup:
    """Тесты для метода assign_task_to_node()."""

    @pytest.mark.asyncio
    async def test_assign_creates_bucket_entries(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Создаёт записи в корзине при назначении группы задач."""
        _, work_item = project_and_work_item

        # Create TaskGroup and Tasks
        tg = TaskGroup(name="Steel 4mm", work_item_id=work_item.id)
        session.add(tg)
        session.flush()

        tasks = [
            TaskItem(
                file_name=f"task_{i}.gnc",
                file_path=f"/path/task_{i}.gnc",
                work_item_id=work_item.id,
                mat_type_id=material.id,
                task_group_id=tg.id,
            )
            for i in range(3)
        ]
        for task in tasks:
            session.add(task)
        session.commit()

        # Assign TaskGroup to node
        system.assign_task_group_to_node(tg.id, "LASER_1")
        session.commit()

        # Check bucket entries
        entries = system.get_bucket("LASER_1")
        assert len(entries) == 3
        for e in entries:
            session.refresh(e)
            assert e.node_id == "LASER_1"


class TestTaskBoardSystemStartTask:
    """Тесты для метода start_task()."""

    def test_start_task(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Начинает выполнение задачи."""
        _, work_item = project_and_work_item

        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            status=TaskItemStatus.PLANNED,
        )
        session.add(task)
        session.commit()

        result = system.start_task(task.id)
        session.commit()
        session.refresh(result)

        assert result.status == TaskItemStatus.IN_PROGRESS
        assert result.started_at is not None

    def test_start_task_invalid_transition(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Ошибка при недопустимом переходе."""
        _, work_item = project_and_work_item

        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            status=TaskItemStatus.DONE,
        )
        session.add(task)
        session.commit()

        with pytest.raises(ValueError, match="Invalid transition"):
            system.start_task(task.id)


class TestTaskBoardSystemPauseTask:
    """Тесты для метода pause_task()."""

    def test_pause_task(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Ставит задачу на паузу."""
        _, work_item = project_and_work_item

        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            status=TaskItemStatus.IN_PROGRESS,
        )
        session.add(task)
        session.commit()

        result = system.pause_task(task.id, reason="Перерыв на обед")
        session.commit()
        session.refresh(result)

        assert result.status == TaskItemStatus.ON_HOLD


class TestTaskBoardSystemSuspendTask:
    """Тесты для метода suspend_task()."""

    def test_suspend_task(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Приостанавливает задачу."""
        _, work_item = project_and_work_item

        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            status=TaskItemStatus.IN_PROGRESS,
        )
        session.add(task)
        session.commit()

        result = system.suspend_task(task.id)
        session.commit()
        session.refresh(result)

        assert result.status == TaskItemStatus.SUSPENDED


class TestTaskBoardSystemCompleteTask:
    """Тесты для метода complete_task()."""

    def test_complete_task(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Завершает задачу."""
        _, work_item = project_and_work_item

        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            status=TaskItemStatus.IN_PROGRESS,
            started_at=datetime.now() - timedelta(minutes=30),
            estimated_minutes=60,
        )
        session.add(task)
        session.commit()

        result = system.complete_task(task.id, sheets_done=5, qty_produced=50)
        session.commit()
        session.refresh(result)

        assert result.status == TaskItemStatus.DONE
        assert result.sheets_done == 5
        assert result.qty_produced == 50
        assert result.completed_at is not None

    def test_complete_task_calculates_actual_minutes(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Вычисляет actual_minutes при завершении."""
        _, work_item = project_and_work_item

        started = datetime.now() - timedelta(minutes=90)
        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            status=TaskItemStatus.IN_PROGRESS,
            started_at=started,
            estimated_minutes=60,
        )
        session.add(task)
        session.commit()

        result = system.complete_task(task.id, sheets_done=5, qty_produced=50)
        session.commit()
        session.refresh(result)

        assert result.actual_minutes is not None
        assert result.actual_minutes >= 89  # ~90 минут

    def test_complete_task_auto_qty_produced(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Auto-calculate qty_produced from TaskParts."""
        _, work_item = project_and_work_item

        task = TaskItem(
            file_name="test.gnc",
            file_path="test.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            sheet_qty=8,
            status=TaskItemStatus.IN_PROGRESS,
            started_at=datetime.now(),
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.id is not None

        # Add TaskParts: 2 parts per sheet
        p1 = TaskPart(task_item_id=task.id, part_sku="BASE-A", qty=2)
        session.add(p1)
        session.commit()

        result = system.complete_task(task.id, sheets_done=4, qty_produced=0)
        session.commit()
        session.refresh(result)

        assert result.qty_produced == 8  # 2 parts * 4 sheets

    def test_complete_task_creates_pallet(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """When create_pallet=True, a ProductionUnit is created."""
        _, work_item = project_and_work_item

        task = TaskItem(
            file_name="test.gnc",
            file_path="test.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            sheet_qty=8,
            status=TaskItemStatus.IN_PROGRESS,
            started_at=datetime.now(),
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.id is not None

        # Mock production_system to capture the call
        calls = []

        class MockProdSys:
            def register_finished_pallet(self, task_item_id, quantity, author_name):
                calls.append({"task_item_id": task_item_id, "quantity": quantity})

        system.production_system = MockProdSys()  # type: ignore[assignment]

        result = system.complete_task(task.id, sheets_done=8, qty_produced=0, create_pallet=True)
        session.commit()
        session.refresh(result)

        assert result.status == TaskItemStatus.DONE
        assert len(calls) == 1
        assert calls[0]["quantity"] == 8  # auto-calculated


class TestTaskBoardSystemGetDrift:
    """Тесты для метода get_drift()."""

    def test_get_drift(self, system: TaskBoardSystem):
        """Вычисляет отклонение от оценки."""
        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=1,
            estimated_minutes=60,
            actual_minutes=90,
        )

        drift = system.get_drift(task)

        assert drift == 50.0  # 50% перерасход

    def test_get_drift_no_estimate(self, system: TaskBoardSystem):
        """Возвращает 0, если нет оценки."""
        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=1,
            estimated_minutes=None,
            actual_minutes=90,
        )

        drift = system.get_drift(task)

        assert drift == 0.0


class TestTaskBoardSystemIncrementSheets:
    """Тесты для метода increment_sheets()."""

    def test_increment_sheets(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Увеличивает счётчик листов."""
        _, work_item = project_and_work_item

        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            sheets_done=0,
        )
        session.add(task)
        session.commit()

        result = system.increment_sheets(task.id)
        session.commit()

        assert result == 1

        task_updated = session.get(TaskItem, task.id)
        assert task_updated.sheets_done == 1


class TestTaskBoardSystemMoveWorkItem:
    """Тесты для метода move_work_item_to_project()."""

    def test_move_work_item_to_project(
        self,
        system: TaskBoardSystem,
        session: Session,
    ):
        """Перемещает WorkItem в другой проект."""
        p1 = Project(name="P1")
        p2 = Project(name="P2")
        session.add_all([p1, p2])
        session.commit()

        wi = WorkItem(folder_name="WI-1", folder_path="wi1", project_id=p1.id)
        session.add(wi)
        session.commit()

        system.move_work_item_to_project(wi.id, p2.id)
        session.commit()

        moved = session.get(WorkItem, wi.id)
        assert moved.project_id == p2.id


class TestTaskBoardSystemAssignTaskGroup:
    """Тесты для метода assign_task_group_to_node()."""

    def test_assign_task_group_to_node(
        self,
        system: TaskBoardSystem,
        session: Session,
    ):
        """Назначает все задачи группы на узел."""
        project = Project(name="Test")
        session.add(project)
        session.commit()

        wi = WorkItem(folder_name="WI-1", folder_path="wi1", project_id=project.id)
        session.add(wi)
        session.commit()
        session.refresh(wi)

        tg = TaskGroup(name="TG-1", work_item_id=wi.id)
        session.add(tg)
        session.commit()
        session.refresh(tg)

        task = TaskItem(
            work_item_id=wi.id,
            task_group_id=tg.id,
            file_name="test.gnc",
            file_path="test.gnc",
        )
        session.add(task)
        session.commit()

        system.assign_task_group_to_node(tg.id, "node2")
        session.commit()

        updated = session.get(TaskItem, task.id)
        assert updated.assigned_to_node == "node2"


class TestTaskBoardSystemAutoReservation:
    """Тесты для авто-резервирования материала при назначении на узел."""

    def test_assign_task_group_calls_create_reservation(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Назначение TaskGroup на узел должно вызывать create_reservation."""
        _, wi = project_and_work_item

        tg = TaskGroup(name="TG-1", work_item_id=wi.id)
        session.add(tg)
        session.commit()
        session.refresh(tg)

        task = TaskItem(
            work_item_id=wi.id,
            task_group_id=tg.id,
            file_name="test.gnc",
            file_path="test.gnc",
            mat_type_id=material.id,
            sheet_qty=5,
        )
        session.add(task)
        session.commit()

        # system.inventory_system — это MagicMock из фикстуры
        system.assign_task_group_to_node(tg.id, "LASER_1")

        # Проверяем, что create_reservation был вызван
        system.inventory_system.create_reservation.assert_called_once()
