from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest

pytest.importorskip("nicegui")

from docuflow.domain.entities.production import PartLibrary, TaskItem, TaskPart
from docuflow.lib.widgets.nest_preview import NestPreview


def _make_scope(session):
    @asynccontextmanager
    async def scope():
        class Req:
            async def get(self, cls):
                return session

        yield Req()

    return scope


@pytest.fixture
def mock_session():
    session = MagicMock()
    part = PartLibrary(id=1, sku="P001", version="A", bbox_x=100, bbox_y=50)
    result = MagicMock()
    result.first.return_value = part
    session.exec.return_value = result
    return session


async def test_nest_preview_generates_svg(mock_session):
    task = TaskItem(
        id=1,
        work_item_id=1,
        file_name="test.gnc",
        file_path="test.gnc",
        sheet_x=3000,
        sheet_y=1500,
        parts=[TaskPart(id=1, task_item_id=1, part_sku="P001", qty=2)],
    )
    preview = NestPreview(task, system_scope=_make_scope(mock_session))
    svg = await preview._generate_svg()
    assert "<svg" in svg
    assert "<rect" in svg
    assert "P001" in svg
