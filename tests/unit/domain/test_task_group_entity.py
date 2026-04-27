from docuflow.domain.entities.production import TaskGroup


def test_task_group_has_required_fields():
    tg = TaskGroup(name="Test Group", work_item_id=1, grouping_rule="manual")
    assert tg.name == "Test Group"
    assert tg.work_item_id == 1
    assert tg.grouping_rule == "manual"
    assert tg.created_by is None
