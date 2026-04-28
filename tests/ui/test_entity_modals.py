import pytest

pytest.importorskip("nicegui")

from docuflow.domain.entities.production import (
    ProductionUnit,
    Project,
    TaskGroup,
    TaskItem,
    WorkItem,
)
from docuflow.lib.widgets.entity_modals import (
    PalletModal,
    ProjectModal,
    TaskGroupModal,
    TaskItemModal,
    WorkItemModal,
)


def test_project_modal_init():
    p = Project(name="Test")
    m = ProjectModal(p, on_save=lambda **kw: None, system_scope=None)
    assert m.project.name == "Test"


def test_work_item_modal_init():
    wi = WorkItem(folder_name="WI-1")
    m = WorkItemModal(wi, projects=[], on_save=lambda **kw: None, system_scope=None)
    assert m.work_item.folder_name == "WI-1"


def test_task_group_modal_init():
    tg = TaskGroup(name="TG-1")
    m = TaskGroupModal(
        tg,
        nodes=["node-a", "node-b"],
        on_assign=lambda **kw: None,
        on_split=lambda **kw: None,
        system_scope=None,
    )
    assert m.task_group.name == "TG-1"


def test_task_item_modal_init():
    task = TaskItem(file_name="test.gnc", file_path="test.gnc")
    m = TaskItemModal(task, on_action=lambda **kw: None, system_scope=None)
    assert m.task_item.file_name == "test.gnc"


def test_pallet_modal_init():
    pallet = ProductionUnit(label_id="P-001")
    m = PalletModal(pallet, on_ship=lambda **kw: None, system_scope=None)
    assert m.pallet.label_id == "P-001"
