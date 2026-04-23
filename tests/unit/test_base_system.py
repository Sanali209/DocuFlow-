"""TDD Tests for BaseSystem CRUD helpers.

Target: src/docuflow/application/base.py
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import Project
from docuflow.infrastructure.config import Config


@pytest.fixture
def base_system():
    """Provide a BaseSystem with an in-memory SQLite session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield BaseSystem(Config(), session)


class TestFindOne:
    """RED: find_one should return first match or None."""

    def test_returns_matching_object(self, base_system):
        project = Project(name="Alpha")
        base_system.db_session.add(project)
        base_system.db_session.commit()

        result = base_system.find_one(Project, name="Alpha")
        assert result is not None
        assert result.name == "Alpha"

    def test_returns_none_when_not_found(self, base_system):
        result = base_system.find_one(Project, name="NonExistent")
        assert result is None

    def test_returns_none_on_empty_table(self, base_system):
        result = base_system.find_one(Project, name="Anything")
        assert result is None


class TestFindAll:
    """RED: find_all should return all matching rows."""

    def test_returns_all_when_no_filter(self, base_system):
        base_system.db_session.add(Project(name="A"))
        base_system.db_session.add(Project(name="B"))
        base_system.db_session.commit()

        results = base_system.find_all(Project)
        assert len(results) == 2

    def test_filters_by_kwargs(self, base_system):
        base_system.db_session.add(Project(name="Target"))
        base_system.db_session.add(Project(name="Other"))
        base_system.db_session.commit()

        results = base_system.find_all(Project, name="Target")
        assert len(results) == 1
        assert results[0].name == "Target"

    def test_returns_empty_list_when_no_match(self, base_system):
        results = base_system.find_all(Project, name="Nope")
        assert results == []


class TestSave:
    """RED: save should persist object and optionally refresh."""

    def test_persists_object(self, base_system):
        project = Project(name="Saved")
        result = base_system.save(project)
        assert result.id is not None

    def test_refreshes_by_default(self, base_system):
        project = Project(name="Refreshed")
        result = base_system.save(project)
        assert result.id is not None  # refresh populates id

    def test_skip_refresh_when_false(self, base_system):
        project = Project(name="NoRefresh")
        result = base_system.save(project, refresh=False)
        # Object is persisted but may not have id in session
        count = base_system.db_session.exec(select(Project)).all()
        assert len(count) == 1


class TestDelete:
    """RED: delete should remove object from database."""

    def test_removes_object(self, base_system):
        project = Project(name="ToDelete")
        base_system.save(project)
        base_system.delete(project)

        result = base_system.find_one(Project, name="ToDelete")
        assert result is None

    def test_delete_only_target(self, base_system):
        base_system.save(Project(name="Keep"))
        to_delete = Project(name="Remove")
        base_system.save(to_delete)

        base_system.delete(to_delete)
        assert base_system.find_one(Project, name="Keep") is not None
        assert base_system.find_one(Project, name="Remove") is None


class TestCount:
    """RED: count should return number of matching rows."""

    def test_returns_zero_on_empty(self, base_system):
        assert base_system.count(Project) == 0

    def test_returns_total(self, base_system):
        base_system.save(Project(name="One"))
        base_system.save(Project(name="Two"))
        assert base_system.count(Project) == 2

    def test_filters_by_kwargs(self, base_system):
        base_system.save(Project(name="Match"))
        base_system.save(Project(name="Other"))
        assert base_system.count(Project, name="Match") == 1
        assert base_system.count(Project, name="Other") == 1
        assert base_system.count(Project, name="Nope") == 0


class TestErrorHandling:
    """RED: methods should raise when session is missing."""

    def test_find_one_without_session_raises(self):
        system = BaseSystem(Config())
        with pytest.raises(RuntimeError):
            system.find_one(Project, name="X")

    def test_save_without_session_raises(self):
        system = BaseSystem(Config())
        with pytest.raises(RuntimeError):
            system.save(Project(name="X"))
