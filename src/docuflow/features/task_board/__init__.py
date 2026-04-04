"""
Модуль task_board — управление батчами и задачами операторов.

Экспортирует:
- TaskBoardSystem — система управления задачами операторов
- BatchEngine — движок группировки задач
- BatchRule — правила группировки
- BatchGroup — группа задач
- StockAlert — предупреждение о запасах
"""

from .system import TaskBoardSystem
from .batch_engine import BatchEngine, BatchRule, BatchGroup, StockAlert

__all__ = [
    "TaskBoardSystem",
    "BatchEngine",
    "BatchRule",
    "BatchGroup",
    "StockAlert",
]
