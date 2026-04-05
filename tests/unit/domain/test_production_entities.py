from datetime import datetime

from docuflow.domain.entities.production import (
    ChatMessage,
    MaterialType,
    ProductionUnit,
    TaskItem,
    WorkItemStatus,
)


def test_work_item_status_pending_cuts():
    """Test 1: WorkItemStatus covers all architectural cases including PENDING_CUTS."""
    assert WorkItemStatus.PENDING_CUTS != WorkItemStatus.NEW
    assert WorkItemStatus.PENDING_CUTS.value == "pending_cuts"


def test_task_item_relative_path():
    """Test 2: file_path should always be stored as a relative path, never absolute."""
    # This is a domain-level expectation; the scanner will enforce it,
    # but the entity should at least support being initialized with relative paths.
    task = TaskItem(
        file_name="01-01-ST37.GNC",
        file_path="sidra\\SIDRA-353203\\01-01-ST37.GNC",
        work_item_id=1,
        scanned_at=datetime.now(),
    )
    assert not task.file_path.startswith("Z:")
    assert not task.file_path.startswith("C:")


def test_production_unit_pre_system():
    """Test 3: ProductionUnit should support pre-system pallets (task_item_id=None)."""
    unit = ProductionUnit(
        label_id="25-07-А-001", task_item_id=None, is_pre_system=True, qty_produced=50
    )
    assert unit.task_item_id is None
    assert unit.is_pre_system is True


def test_material_type_time_params():
    """Test 4: MaterialType should contain the physical parameters used for time estimation."""
    mat = MaterialType(code="AA 5052-H32", thickness=3.0)
    # Checking default values defined in architectural specs
    assert mat.cut_speed_mm_per_min == 3000.0
    assert mat.time_tolerance_pct == 15.0


def test_chat_message_tree():
    """Test 5: ChatMessage should support a tree-like hierarchy via parent_message_id."""
    parent = ChatMessage(
        id=1, author="user1", message_type="MESSAGE", content="Hello", node_id="MASTER"
    )
    child = ChatMessage(
        id=2,
        author="user2",
        message_type="MESSAGE",
        content="Hi",
        node_id="SLAVE_1",
        parent_message_id=1,
    )
    assert child.parent_message_id == parent.id
