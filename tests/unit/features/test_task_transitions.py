from docuflow.domain.entities.production import TaskItemStatus
from docuflow.features.task_board.system import TaskBoardSystem


def test_suspended_transitions():
    tbs = TaskBoardSystem.__new__(TaskBoardSystem)
    allowed = tbs.VALID_TASK_TRANSITIONS[TaskItemStatus.IN_PROGRESS]
    assert TaskItemStatus.SUSPENDED in allowed
    assert TaskItemStatus.DONE in tbs.VALID_TASK_TRANSITIONS[TaskItemStatus.SUSPENDED]
