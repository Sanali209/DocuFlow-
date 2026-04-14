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
    TaskItem,
    TaskItemStatus,
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
    return TaskBoardSystem(config=config, db_engine=engine, session=session)


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


class TestTaskBoardSystemLockBatch:
    """Тесты для метода lock_batch()."""

    @pytest.mark.asyncio
    async def test_lock_batch_creates_entries(
        self,
        system: TaskBoardSystem,
        project_and_work_item,
        material: MaterialType,
        session: Session,
    ):
        """Создаёт записи в корзине при блокировке батча."""
        _, work_item = project_and_work_item

        tasks = [
            TaskItem(
                file_name=f"task_{i}.gnc",
                file_path=f"/path/task_{i}.gnc",
                work_item_id=work_item.id,
                mat_type_id=material.id,
                batch_group_id="test_batch",
            )
            for i in range(3)
        ]
        for task in tasks:
            session.add(task)
        session.commit()

        entries = await system.lock_batch("test_batch", "LASER_1", "operator1")
        session.commit()  # Sync session after system call

        assert len(entries) == 3
        for e in entries:
            session.refresh(e)
            assert e.node_id == "LASER_1"
            assert e.assigned_user == "operator1"


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
