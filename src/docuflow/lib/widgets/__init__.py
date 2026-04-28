"""
Библиотека переиспользуемых UI виджетов для DocuFlow.

Teal Industrial Design System компоненты.
"""

# Новые компоненты
# Существующие компоненты
from .batch_card import BatchCard, TaskItemRow
from .bucket_panel import BucketPanel
from .button import GhostBtn, PrimaryBtn, SecondaryBtn
from .card import Card
from .explorer_button import ExplorerButton
from .file_changed_alert import FileChangedAlert
from .hierarchy_row import HierarchyRow
from .hierarchy_table import HierarchyTable
from .info_row import InfoGrid, InfoPair, InfoRow
from .input import CheckboxLabel, InputLabel, SelectLabel, SwitchLabel, TextareaLabel
from .kpi_card import KPICard, KPIGrid
from .ns_mirror_status import NSMirrorStatus
from .part_preview import PartPreview
from .scan_log_panel import ScanLogPanel
from .status_badge import StatusBadge
from .status_indicator import StatusIndicator
from .surface import Surface, SurfaceCard, SurfaceSection
from .ui_utils import (
    ConfirmDialog,
    EmptyState,
    ErrorState,
    LoadingSkeleton,
    LoadingSpinner,
    NotifyHelper,
)

__all__ = [
    # Существующие
    "BatchCard",
    "BucketPanel",
    # Containers
    "Card",
    "CheckboxLabel",
    "ConfirmDialog",
    "EmptyState",
    "ErrorState",
    "ExplorerButton",
    "FileChangedAlert",
    "GhostBtn",
    "HierarchyRow",
    "HierarchyTable",
    "InfoGrid",
    "InfoPair",
    # Data display
    "InfoRow",
    # Inputs
    "InputLabel",
    "KPICard",
    "KPIGrid",
    "LoadingSkeleton",
    # UI utilities
    "LoadingSpinner",
    "NSMirrorStatus",
    "NotifyHelper",
    "PartPreview",
    # Новые компоненты - buttons
    "PrimaryBtn",
    "ScanLogPanel",
    "SecondaryBtn",
    "SelectLabel",
    "StatusBadge",
    # Status
    "StatusIndicator",
    "Surface",
    "SurfaceCard",
    "SurfaceSection",
    "SwitchLabel",
    "TaskItemRow",
    "TextareaLabel",
]
