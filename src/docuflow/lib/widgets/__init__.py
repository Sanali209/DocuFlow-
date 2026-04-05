"""
Библиотека переиспользуемых UI виджетов для DocuFlow.

Экспортирует:
- StatusBadge — цветные бейджи статусов
- ExplorerButton — кнопка "Открыть в Explorer"
- FileChangedAlert — баннер уведомления об изменении файла
- ScanLogPanel — live лог сканера (уже существует)
- NSMirrorStatus — индикатор синхронизации NS (уже существует)
- BatchCard — карточка батча
- TaskItemRow — строка задачи с прогресс-баром
- BucketPanel — корзина оператора
"""

from .batch_card import BatchCard, TaskItemRow
from .bucket_panel import BucketPanel
from .explorer_button import ExplorerButton
from .file_changed_alert import FileChangedAlert
from .ns_mirror_status import NSMirrorStatus

# from .work_item_card import WorkItemCard
from .part_preview import PartPreview
from .scan_log_panel import ScanLogPanel
from .status_badge import StatusBadge

__all__ = [
    "BatchCard",
    "BucketPanel",
    "ExplorerButton",
    "FileChangedAlert",
    "NSMirrorStatus",
    "PartPreview",
    "ScanLogPanel",
    "StatusBadge",
    "TaskItemRow",
    "WorkItemCard",
]
