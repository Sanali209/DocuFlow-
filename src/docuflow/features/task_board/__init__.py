"""
Модуль task_board — управление батчами и задачами операторов.

Экспортирует:
- TaskBoardSystem — система управления задачами операторов
- TaskGroupService — сервис группировки задач
- StockAlert — предупреждение о запасах
"""

from .system import TaskBoardSystem
from .task_group_service import StockAlert, TaskGroupService

__all__ = [
    "StockAlert",
    "TaskBoardSystem",
    "TaskGroupService",
]
