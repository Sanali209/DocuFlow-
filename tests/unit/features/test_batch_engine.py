"""
Тесты для BatchEngine.

TDD подход:
1. Сначала тесты
2. Потом код
3. Рефакторинг
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import (
    MaterialType,
    Project,
    TaskItem,
    WorkItem,
)
from docuflow.features.task_board.batch_engine import BatchEngine, BatchRule


@pytest.fixture(name="session")
def session_fixture():
    """Создаёт in-memory SQLite сессию для тестов."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="engine")
def engine_fixture(session: Session):
    """Создаёт экземпляр BatchEngine."""
    return BatchEngine(session)


@pytest.fixture(name="material")
def material_fixture(session: Session):
    """Создаёт тестовый материал."""
    mat = MaterialType(
        code="ST37",
        thickness=3.0,
        nominal_x=3000,
        nominal_y=1500,
    )
    session.add(mat)
    session.commit()
    session.refresh(mat)
    return mat


class TestBatchEngineCompute:
    """Тесты для метода compute()."""

    def test_single_material_one_batch(self, engine: BatchEngine, material: MaterialType):
        """Задачи с одним материалом → один батч."""
        tasks = [
            TaskItem(
                file_name=f"task_{i}.gnc",
                file_path=f"/path/task_{i}.gnc",
                mat_type_id=material.id,
                thickness=3.0,
                sheet_x=3000,
                sheet_y=1500,
            )
            for i in range(3)
        ]

        groups = engine.compute(tasks, BatchRule())

        assert len(groups) == 1
        assert len(groups[0].tasks) == 3
        assert groups[0].mat_type_id == material.id

    def test_different_materials_separate_batches(self, engine: BatchEngine, session: Session):
        """Разные материалы → разные батчи."""
        mat1 = MaterialType(code="ST37", thickness=3.0, nominal_x=3000, nominal_y=1500)
        mat2 = MaterialType(code="S235", thickness=2.0, nominal_x=2000, nominal_y=1000)
        session.add(mat1)
        session.add(mat2)
        session.commit()

        tasks = [
            TaskItem(
                file_name="task_1.gnc",
                file_path="/path/task_1.gnc",
                mat_type_id=mat1.id,
                thickness=3.0,
                sheet_x=3000,
                sheet_y=1500,
            ),
            TaskItem(
                file_name="task_2.gnc",
                file_path="/path/task_2.gnc",
                mat_type_id=mat2.id,
                thickness=2.0,
                sheet_x=2000,
                sheet_y=1000,
            ),
        ]

        groups = engine.compute(tasks, BatchRule())

        assert len(groups) == 2

    def test_tasks_sorted_by_step_batch_index(self, engine: BatchEngine, material: MaterialType):
        """Задачи сортируются по step_index → batch_index."""
        tasks = [
            TaskItem(
                file_name="task_1.gnc",
                file_path="/path/task_1.gnc",
                mat_type_id=material.id,
                thickness=3.0,
                sheet_x=3000,
                sheet_y=1500,
                step_index=2,
                batch_index=1,
            ),
            TaskItem(
                file_name="task_2.gnc",
                file_path="/path/task_2.gnc",
                mat_type_id=material.id,
                thickness=3.0,
                sheet_x=3000,
                sheet_y=1500,
                step_index=1,
                batch_index=1,
            ),
            TaskItem(
                file_name="task_3.gnc",
                file_path="/path/task_3.gnc",
                mat_type_id=material.id,
                thickness=3.0,
                sheet_x=3000,
                sheet_y=1500,
                step_index=1,
                batch_index=2,
            ),
        ]

        groups = engine.compute(tasks, BatchRule())

        assert len(groups) == 1
        steps = [(t.step_index, t.batch_index) for t in groups[0].tasks]
        assert steps == [(1, 1), (1, 2), (2, 1)]

    def test_empty_tasks(self, engine: BatchEngine):
        """Пустой список задач → пустой список батчей."""
        groups = engine.compute([], BatchRule())

        assert len(groups) == 0

    def test_max_batch_size(self, engine: BatchEngine, material: MaterialType):
        """Ограничение размера батча."""
        tasks = [
            TaskItem(
                file_name=f"task_{i}.gnc",
                file_path=f"/path/task_{i}.gnc",
                mat_type_id=material.id,
                thickness=3.0,
                sheet_x=3000,
                sheet_y=1500,
            )
            for i in range(5)
        ]

        groups = engine.compute(tasks, BatchRule(max_batch_size=2))

        assert len(groups) == 1
        assert len(groups[0].tasks) == 2


class TestBatchEngineApplyBatches:
    """Тесты для метода apply_batches()."""

    def test_apply_batches(self, engine: BatchEngine, session: Session, material: MaterialType):
        """Применяет батчи к БД."""
        # Создаём WorkItem и TaskItem
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

        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            thickness=3.0,
            sheet_x=3000,
            sheet_y=1500,
        )
        session.add(task)
        session.commit()

        # Группируем и применяем
        groups = engine.compute([task], BatchRule())
        engine.apply_batches(groups, session)

        # Проверяем, что batch_group_id установлен
        task_updated = session.get(TaskItem, task.id)
        assert task_updated.batch_group_id is not None


class TestBatchEngineMoveTask:
    """Тесты для метода move_task()."""

    def test_move_task(self, engine: BatchEngine, session: Session, material: MaterialType):
        """Перемещает задачу в другой батч."""
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

        task = TaskItem(
            file_name="task.gnc",
            file_path="/path/task.gnc",
            work_item_id=work_item.id,
            mat_type_id=material.id,
            thickness=3.0,
            sheet_x=3000,
            sheet_y=1500,
            batch_group_id="old_batch",
        )
        session.add(task)
        session.commit()

        result = engine.move_task(task.id, "new_batch", session)

        assert result.batch_group_id == "new_batch"

    def test_move_task_not_found(self, engine: BatchEngine, session: Session):
        """Ошибка, если задача не найдена."""
        with pytest.raises(ValueError, match="не найдена"):
            engine.move_task(999999, "new_batch", session)


class TestBatchEngineCreateBatch:
    """Тесты для метода create_batch()."""

    def test_create_batch(self, engine: BatchEngine, session: Session, material: MaterialType):
        """Создаёт новый батч для списка задач."""
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

        tasks = []
        for i in range(3):
            task = TaskItem(
                file_name=f"task_{i}.gnc",
                file_path=f"/path/task_{i}.gnc",
                work_item_id=work_item.id,
                mat_type_id=material.id,
                thickness=3.0,
                sheet_x=3000,
                sheet_y=1500,
            )
            session.add(task)
            session.commit()
            tasks.append(task)

        batch_id = engine.create_batch([t.id for t in tasks], session)

        # Проверяем, что все задачи получили batch_group_id
        for task in tasks:
            task_updated = session.get(TaskItem, task.id)
            assert task_updated.batch_group_id == batch_id


class TestBatchEngineSplitBatch:
    """Тесты для метода split_batch()."""

    def test_split_batch(self, engine: BatchEngine, session: Session, material: MaterialType):
        """Разделяет батч на два."""
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

        tasks = []
        for i in range(3):
            task = TaskItem(
                file_name=f"task_{i}.gnc",
                file_path=f"/path/task_{i}.gnc",
                work_item_id=work_item.id,
                mat_type_id=material.id,
                thickness=3.0,
                sheet_x=3000,
                sheet_y=1500,
                batch_group_id="original_batch",
            )
            session.add(task)
            session.commit()
            tasks.append(task)

        new_batch_id = engine.split_batch("original_batch", [tasks[0].id, tasks[1].id], session)

        # Проверяем, что задачи разделены
        task0 = session.get(TaskItem, tasks[0].id)
        task1 = session.get(TaskItem, tasks[1].id)
        task2 = session.get(TaskItem, tasks[2].id)

        assert task0.batch_group_id == new_batch_id
        assert task1.batch_group_id == new_batch_id
        assert task2.batch_group_id == "original_batch"
