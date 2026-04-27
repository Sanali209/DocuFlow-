from docuflow.domain.entities.production import TaskItemStatus


def test_suspended_status_exists():
    assert hasattr(TaskItemStatus, "SUSPENDED")
    assert TaskItemStatus.SUSPENDED == "suspended"
