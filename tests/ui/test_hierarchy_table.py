import pytest

pytest.importorskip("nicegui")

from docuflow.lib.widgets.hierarchy_row import HierarchyRow
from docuflow.lib.widgets.hierarchy_table import HierarchyTable


def test_hierarchy_row_renders(ui_context):
    row = HierarchyRow(icon="folder", title="Test", system_scope=None)
    result = row.render()
    assert result is not None


def test_hierarchy_table_instantiates():
    table = HierarchyTable(user_id="admin", view_name="test", system_scope=None)
    assert table.user_id == "admin"
    assert table.view_name == "test"
