"""
StatusBadge — цветной бейдж для отображения статусов WorkItem и TaskItem.

Используется в таблицах, карточках и других views.
"""

from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import TaskItemStatus, WorkItemStatus
from docuflow.lib.base_widget import BaseDocuWidget

# Цветовая схема для статусов WorkItem
WORK_ITEM_COLORS: dict[WorkItemStatus, str] = {
    WorkItemStatus.NEW: "blue",
    WorkItemStatus.PENDING_CUTS: "orange",
    WorkItemStatus.FOLDER_NO_DOC: "orange",
    WorkItemStatus.DOC_NO_FOLDER: "orange",
    WorkItemStatus.REGISTERED: "teal",
    WorkItemStatus.IN_PROGRESS: "green",
    WorkItemStatus.ON_HOLD: "yellow",
    WorkItemStatus.BLOCKED: "red",
    WorkItemStatus.DONE: "gray",
    WorkItemStatus.CANCELLED: "darkgray",
    WorkItemStatus.ARCHIVED: "darkgray",
}

# Цветовая схема для статусов TaskItem
TASK_ITEM_COLORS: dict[TaskItemStatus, str] = {
    TaskItemStatus.PLANNED: "blue",
    TaskItemStatus.IN_PROGRESS: "green",
    TaskItemStatus.ON_HOLD: "yellow",
    TaskItemStatus.DONE: "gray",
    TaskItemStatus.CANCELLED: "darkgray",
    TaskItemStatus.BLOCKED: "red",
}


class StatusBadge(BaseDocuWidget):
    """
    Цветной бейдж для отображения статуса.

    Props:
        status: WorkItemStatus | TaskItemStatus — статус для отображения
        size: str — размер ("sm", "md", "lg")
        system_scope: Any — провайдер систем (опционально)
    """

    def __init__(
        self, status: WorkItemStatus | TaskItemStatus, size: str = "md", system_scope: Any = None
    ):
        super().__init__(system_scope)
        self.status = status
        self.size = size

    def render(self) -> ui.badge:
        """Рендерит бейдж с цветом и текстом."""
        color = self._get_color()
        label = self._get_label()

        size_classes = {
            "sm": "text-xs px-1.5 py-0.5",
            "md": "text-sm px-2 py-1",
            "lg": "text-base px-3 py-1.5",
        }

        return ui.badge(label).props(f"color={color} {size_classes.get(self.size, '')}")

    def _get_color(self) -> str:
        """Возвращает цвет для статуса."""
        if isinstance(self.status, WorkItemStatus):
            return WORK_ITEM_COLORS.get(self.status, "gray")
        elif isinstance(self.status, TaskItemStatus):
            return TASK_ITEM_COLORS.get(self.status, "gray")
        return "gray"

    def _get_label(self) -> str:
        """Возвращает текстовую метку для статуса."""
        labels = {
            WorkItemStatus.NEW: "Новый",
            WorkItemStatus.PENDING_CUTS: "Ожидание раскроя",
            WorkItemStatus.FOLDER_NO_DOC: "Нет документа",
            WorkItemStatus.DOC_NO_FOLDER: "Нет папки",
            WorkItemStatus.REGISTERED: "Зарегистрирован",
            WorkItemStatus.IN_PROGRESS: "В работе",
            WorkItemStatus.ON_HOLD: "На паузе",
            WorkItemStatus.BLOCKED: "Заблокирован",
            WorkItemStatus.DONE: "Завершён",
            WorkItemStatus.CANCELLED: "Отменён",
            WorkItemStatus.ARCHIVED: "Архивирован",
            TaskItemStatus.PLANNED: "Запланирован",
            TaskItemStatus.IN_PROGRESS: "В работе",
            TaskItemStatus.ON_HOLD: "На паузе",
            TaskItemStatus.DONE: "Завершён",
            TaskItemStatus.CANCELLED: "Отменён",
            TaskItemStatus.BLOCKED: "Заблокирован",
        }
        return labels.get(self.status, str(self.status))
