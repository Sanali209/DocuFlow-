"""TDD Tests for SearchSystem.

Coverage target: features/core/search.py
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import PartLibrary, ProductionUnit, Project, WorkItem
from docuflow.features.core.search import SearchResult, SearchSystem


@pytest.fixture
def search_session():
    """Provide an in-memory SQLite session with test data."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Seed project (required for WorkItem)
        project = Project(name="Test Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        # Seed work items
        session.add(WorkItem(
            project_id=project.id,
            folder_name="SIDRA-123",
            folder_path="./SIDRA-123",
            sidra_number="123",
            work_item_type="SIDRA",
        ))
        session.add(WorkItem(
            project_id=project.id,
            folder_name="SIDRA-456",
            folder_path="./SIDRA-456",
            sidra_number="456",
            work_item_type="SIDRA",
        ))
        session.add(WorkItem(
            project_id=project.id,
            folder_name="OTHER-001",
            folder_path="./OTHER-001",
            sidra_number="999",
            work_item_type="REWORK",
        ))

        # Seed parts
        session.add(PartLibrary(sku="PLATE-10", version="A"))
        session.add(PartLibrary(sku="PLATE-20", version="B"))

        # Seed production units
        session.add(ProductionUnit(label_id="PALLET-A", qty_produced=10))
        session.add(ProductionUnit(label_id="PALLET-B", qty_produced=20))

        session.commit()
        yield session


class TestSearchEmptyQuery:
    """RED: search with empty or short query should return empty list."""

    async def test_empty_query_returns_empty(self, search_session):
        system = SearchSystem(search_session)
        result = await system.search("")
        assert result == []

    async def test_single_char_query_returns_empty(self, search_session):
        system = SearchSystem(search_session)
        result = await system.search("x")
        assert result == []


class TestSearchWorkItems:
    """RED: search should find WorkItems by folder_name or sidra_number."""

    async def test_find_by_folder_name(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("SIDRA")
        assert len(results) >= 2
        types = {r.type for r in results}
        assert "work_item" in types

    async def test_find_by_sidra_number(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("123")
        assert any(r.type == "work_item" and r.title == "SIDRA-123" for r in results)

    async def test_result_has_correct_fields(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("SIDRA-123")
        item = next(r for r in results if r.type == "work_item")
        assert item.title == "SIDRA-123"
        assert item.view_name == "work_items"
        assert item.icon == "assignment"
        assert item.payload == {"folder_name": "SIDRA-123"}


class TestSearchParts:
    """RED: search should find PartLibrary items by SKU."""

    async def test_find_by_sku(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("PLATE")
        assert any(r.type == "part" for r in results)

    async def test_part_result_fields(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("PLATE-10")
        part = next(r for r in results if r.type == "part")
        assert part.title == "PLATE-10"
        assert part.view_name == "parts"
        assert part.icon == "extension"
        assert part.payload == {"sku": "PLATE-10"}


class TestSearchProductionUnits:
    """RED: search should find ProductionUnits by label_id."""

    async def test_find_by_label(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("PALLET")
        assert any(r.type == "pallet" for r in results)

    async def test_pallet_result_fields(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("PALLET-A")
        unit = next(r for r in results if r.type == "pallet")
        assert unit.title == "PALLET-A"
        assert unit.view_name == "production"
        assert unit.icon == "inventory_2"
        assert unit.payload == {"label_id": "PALLET-A"}


class TestSearchLimit:
    """RED: search should respect limit parameter."""

    async def test_limit_cuts_results(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("SIDRA", limit=1)
        assert len(results) <= 1

    async def test_default_limit_is_10(self, search_session):
        system = SearchSystem(search_session)
        results = await system.search("A")
        assert len(results) <= 10


class TestSearchResultStructure:
    """RED: SearchResult dataclass should hold expected fields."""

    def test_dataclass_fields(self):
        sr = SearchResult(
            id=1,
            title="Test",
            subtitle="Sub",
            type="work_item",
            view_name="work_items",
            icon="assignment",
            payload={"key": "val"},
        )
        assert sr.id == 1
        assert sr.title == "Test"
        assert sr.payload == {"key": "val"}
