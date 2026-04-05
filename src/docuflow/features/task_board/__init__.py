"""
Модуль task_board — управление батчами и задачами операторов.

Экспортирует:
- TaskBoardSystem — система управления задачами операторов
- BatchEngine — движок группировки задач
- BatchRule — правила группировки
- BatchGroup — группа задач
- StockAlert — предупреждение о запасах
"""

from .batch_engine import BatchEngine, BatchGroup, BatchRule, StockAlert
from .system import TaskBoardSystem

__all__ = [
    "BatchEngine",
    "BatchGroup",
    "BatchRule",
    "StockAlert",
    "TaskBoardSystem",
]
