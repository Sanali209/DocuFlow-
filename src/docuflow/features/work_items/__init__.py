"""
Модуль work_items — управление рабочими элементами (нарядами).

Экспортирует:
- WorkItemSystem — основная система
- WorkItemsView — UI view для списка нарядов
- WorkItemCard — карточка наряда
- WorkItemStatus — статусы рабочих элементов
- WorkItemType — типы рабочих элементов
- WorkItemFilters — фильтры для списка
"""

from docuflow.domain.entities.production import WorkItemStatus, WorkItemType
from docuflow.lib.widgets.work_item_card import WorkItemCard

from .system import (
    WorkItemFilters,
    WorkItemSystem,
)
from .view import WorkItemsView

__all__ = [
    "WorkItemCard",
    "WorkItemFilters",
    "WorkItemStatus",
    "WorkItemSystem",
    "WorkItemType",
    "WorkItemsView",
]
