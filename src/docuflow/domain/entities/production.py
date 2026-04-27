import datetime
from enum import StrEnum

from sqlmodel import Field, Relationship, UniqueConstraint

from docuflow.domain.entities.base import BaseEntity

# --- ENUMS ---


class WorkItemType(StrEnum):
    SIDRA = "sidra"
    MIHTAV = "mihtav"
    REWORK = "rework"
    LASER = "laser"


class WorkItemStatus(StrEnum):
    NEW = "new"
    PENDING_CUTS = "pending_cuts"
    FOLDER_NO_DOC = "folder_no_doc"
    DOC_NO_FOLDER = "doc_no_folder"
    REGISTERED = "registered"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskItemStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    SUSPENDED = "suspended"
    DONE = "done"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


# --- ENTITIES ---


class Project(BaseEntity, table=True):
    """Container for high-level project grouping (e.g., 'SHLAV-2')."""

    name: str = Field(unique=True, index=True)
    description: str | None = None
    is_default: bool = Field(default=False)
    deadline: datetime.datetime | None = None
    status: str = Field(default="active")

    # Relations
    work_items: list["WorkItem"] = Relationship(back_populates="project")


class WorkItem(BaseEntity, table=True):
    """Represents a workshop order/folder (Symmetric Truth key: folder_name)."""

    project_id: int = Field(foreign_key="project.id", index=True)
    work_item_type: WorkItemType = Field(default=WorkItemType.SIDRA)
    status: WorkItemStatus = Field(default=WorkItemStatus.NEW)

    folder_name: str = Field(unique=True, index=True)
    folder_path: str  # Relative path from scan root

    sidra_number: str | None = None
    sidra_step: str | None = None

    folder_found_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    doc_received_at: datetime.datetime | None = None
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    last_scanned_at: datetime.datetime | None = None

    # Relations
    project: Project | None = Relationship(back_populates="work_items")
    tasks: list["TaskItem"] = Relationship(back_populates="work_item")
    task_groups: list["TaskGroup"] = Relationship(back_populates="work_item")


class TaskGroup(BaseEntity, table=True):
    """A group of TaskItems (replaces batch_group_id)."""

    name: str | None = None
    work_item_id: int = Field(foreign_key="workitem.id", index=True)
    created_by: str | None = None
    grouping_rule: str = Field(default="manual")  # "manual" | "auto_material"

    # Relations
    work_item: WorkItem | None = Relationship(back_populates="task_groups")
    tasks: list["TaskItem"] = Relationship(back_populates="task_group")


class TaskItem(BaseEntity, table=True):
    """Represents a single GNC file (cutting task)."""

    work_item_id: int = Field(foreign_key="workitem.id", index=True)
    task_group_id: int | None = Field(default=None, foreign_key="taskgroup.id", index=True)
    mat_type_id: int | None = Field(default=None, foreign_key="materialtype.id")

    status: TaskItemStatus = Field(default=TaskItemStatus.PLANNED)
    priority: int = Field(default=1)  # 0: Low, 1: Normal, 2: High
    is_urgent: bool = Field(default=False)

    file_name: str
    file_path: str  # Relative path
    file_hash: str | None = None  # MD5 for change detection

    sheet_x: float | None = None
    sheet_y: float | None = None
    sheet_qty: int | None = None
    thickness: float | None = None
    gnc_date: datetime.datetime | None = None

    sheets_done: int = Field(default=0)
    qty_produced: int | None = None

    estimated_minutes: int | None = None
    actual_minutes: int | None = None

    step_index: int | None = None
    batch_index: int | None = None
    batch_group_id: str | None = None  # UUID для группировки в батчи

    assigned_to_node: str | None = None
    scanned_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None

    block_reason: str | None = None

    # Relations
    work_item: WorkItem | None = Relationship(back_populates="tasks")
    task_group: TaskGroup | None = Relationship(back_populates="tasks")
    parts: list["TaskPart"] = Relationship(back_populates="task")
    # Bidirectional link to physical pellets.
    # Named 'task_item' to avoid shadowing the 'task' keyword or internal variables.
    production_units: list["ProductionUnit"] = Relationship(back_populates="task_item")


class TaskPart(BaseEntity, table=True):
    """Links parts from PartLibrary to a specific TaskItem (GNC)."""

    task_item_id: int = Field(foreign_key="taskitem.id", index=True)
    part_sku: str = Field(index=True)
    version: str = Field(default="A")
    qty: int = Field(default=1)

    # We reference the specific library entry by ID (internal) or by SKU+Version (logical)
    part_id: int | None = Field(default=None, foreign_key="partlibrary.id")

    # Relations
    task: TaskItem | None = Relationship(back_populates="parts")
    part: "PartLibrary" = Relationship(back_populates="task_links")


class PartLibrary(BaseEntity, table=True):
    """Global registry of unique physical parts."""

    __table_args__ = (UniqueConstraint("sku", "version"),)

    sku: str = Field(index=True)
    version: str = Field(default="A", index=True)
    mat_type_id: int | None = Field(default=None, foreign_key="materialtype.id")
    name: str | None = None

    bbox_x: float | None = None
    bbox_y: float | None = None
    contour_count: int = Field(default=0)
    corner_count: int = Field(default=0)
    hole_count: int = Field(default=0)

    weight_per_pcs: float | None = None
    svg_preview_path: str | None = None

    first_seen_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    last_seen_at: datetime.datetime | None = None

    # Relations
    task_links: list[TaskPart] = Relationship(back_populates="part")
    templates: list["PartTemplate"] = Relationship(back_populates="part")


class PartTemplate(BaseEntity, table=True):
    """Stored warnings or templates associated with a specific part SKU."""

    part_sku: str = Field(foreign_key="partlibrary.sku", index=True)
    message: str
    severity: str = Field(default="info")  # info, warning, critical
    created_by: str | None = None

    # Relations
    part: PartLibrary | None = Relationship(back_populates="templates")


# --- MATERIALS (Block D) ---


class MaterialFormFactor(StrEnum):
    SHEET = "sheet"
    TUBE = "tube"
    BAR = "bar"
    OTHER = "other"


class MaterialStockStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    ALLOCATED = "allocated"
    CONSUMED = "consumed"
    DEFECT = "defect"


class MaterialType(BaseEntity, table=True):
    """Registry of material specifications and cutting parameters."""

    __table_args__ = (UniqueConstraint("code", "thickness"),)

    code: str = Field(index=True)
    form_factor: MaterialFormFactor = Field(default=MaterialFormFactor.SHEET)
    thickness: float | None = None
    nominal_x: float | None = None
    nominal_y: float | None = None
    weight_per_sheet: float | None = None
    primary_unit: str = Field(default="sheet")

    # Time Estimation Parameters (Editable by Foreman)
    cut_speed_mm_per_min: float = Field(default=3000.0)
    pierce_time_sec: float = Field(default=3.0)
    idle_speed_mm_per_min: float = Field(default=10000.0)
    time_tolerance_pct: float = Field(default=15.0)

    # Relations
    stock_items: list["MaterialStock"] = Relationship(back_populates="material_type")


class MaterialStock(BaseEntity, table=True):
    """Physical material packs/batches in inventory."""

    mat_type_id: int = Field(foreign_key="materialtype.id", index=True)
    status: MaterialStockStatus = Field(default=MaterialStockStatus.AVAILABLE)
    batch_code: str | None = None
    quantity: float = Field(default=0.0)
    quantity_kg: float | None = None
    location: str | None = None

    # Relations
    material_type: MaterialType | None = Relationship(back_populates="stock_items")
    reservations: list["Reservation"] = Relationship(back_populates="stock_item")
    audit_logs: list["MaterialAudit"] = Relationship(back_populates="stock_item")


class Reservation(BaseEntity, table=True):
    """Soft or hard reservation of material for a specific WorkItem."""

    stock_item_id: int = Field(foreign_key="materialstock.id")
    work_item_id: int = Field(foreign_key="workitem.id")
    qty_reserved: float
    reservation_type: str = Field(default="soft")  # soft | hard

    # Relations
    stock_item: MaterialStock | None = Relationship(back_populates="reservations")


class MaterialAudit(BaseEntity, table=True):
    """Traceable history of material movements."""

    stock_item_id: int = Field(foreign_key="materialstock.id", index=True)
    operation: str  # income | write_off | correction | defect | reorder
    qty_delta: float
    qty_kg_delta: float | None = None
    reason: str | None = None
    ref_task_item_id: int | None = Field(default=None, foreign_key="taskitem.id")
    author: str | None = None
    node_id: str | None = None

    # Relations
    stock_item: MaterialStock | None = Relationship(back_populates="audit_logs")


# --- CONSUMABLES (Block E) ---


class Consumable(BaseEntity, table=True):
    """Workshop supplies (nozzles, lenses, tape, etc.)."""

    name: str = Field(unique=True, index=True)
    category: str = Field(default="nozzle")  # nozzle | lens | tape | gas | other
    unit: str = Field(default="pcs")
    quantity: float = Field(default=0.0)
    min_quantity: float = Field(default=0.0)


class ConsumableLog(BaseEntity, table=True):
    """Usage and restocking history for consumables."""

    consumable_id: int = Field(foreign_key="consumable.id", index=True)
    operation: str  # use | restock | write_off
    qty_delta: float
    ref_task_item_id: int | None = Field(default=None, foreign_key="taskitem.id")
    author: str | None = None
    note: str | None = None


# --- LOGISTICS (Block F) ---


class StorageLocation(BaseEntity, table=True):
    """Physical storage place (e.g., 'A-02-3')."""

    code: str = Field(unique=True, index=True)
    name: str | None = None
    is_active: bool = Field(default=True)

    # Relations - tracks units currently stored here
    units: list["ProductionUnit"] = Relationship(back_populates="storage_location")


class ProductionUnit(BaseEntity, table=True):
    """A pallet or container of finished parts."""

    label_id: str = Field(unique=True, index=True)  # Human-readable "YY-MM-Node-Seq"
    task_item_id: int | None = Field(default=None, foreign_key="taskitem.id")
    storage_location_id: int | None = Field(default=None, foreign_key="storagelocation.id")

    qty_produced: int = Field(default=0)
    is_stock: bool = Field(default=False)
    is_pre_system: bool = Field(default=False)
    stock_transferred_at: datetime.datetime | None = None

    parent_label_id: str | None = None  # Traceability for split operations
    created_by: str | None = None

    # Relations: Explicitly defined for SQLModel attribute access.
    # Note: Using '.task_item' instead of '.task' is mandatory to ensure clear
    # distinction from the generic 'TaskItem' class and local task variables.
    task_item: TaskItem | None = Relationship(back_populates="production_units")
    storage_location: StorageLocation | None = Relationship(back_populates="units")


# --- BUCKET (Block G) ---


class WorkerBucketEntry(BaseEntity, table=True):
    """A task assigned to a specific worker/node basket."""

    node_id: str = Field(index=True)
    assigned_user: str | None = None
    task_item_id: int = Field(foreign_key="taskitem.id", index=True)
    task_group_id: int | None = Field(default=None, foreign_key="taskgroup.id")
    # batch_group_id: str | None = None  # UUID for batched tasks — kept for Phase 9 cleanup

    locked_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    handover_note: str | None = None
    handover_at: datetime.datetime | None = None
    handover_from: str | None = None


# --- LOGS & COMMUNICATION (Block H) ---


class WorkLogType(StrEnum):
    INFO = "info"
    WARNING = "warning"
    FILE_CHANGED = "file_changed"
    STATUS_CHANGE = "status_change"
    ON_HOLD = "on_hold"
    HANDOVER = "handover"
    STOCK_ALERT = "stock_alert"
    SCAN_ERROR = "scan_error"
    BLOCKED = "blocked"
    EMPTY_FOLDER = "empty_folder"
    NS_MIRROR = "ns_mirror"
    MATERIAL_REMOVED = "material_removed"


class WorkLog(BaseEntity, table=True):
    """Generic traceability log for work items and tasks."""

    work_item_id: int | None = Field(default=None, foreign_key="workitem.id", index=True)
    task_item_id: int | None = Field(default=None, foreign_key="taskitem.id", index=True)
    log_type: WorkLogType = Field(default=WorkLogType.INFO)
    author: str | None = None
    node_id: str | None = None
    message: str
    payload: str | None = None  # JSON string


class IncidentLog(BaseEntity, table=True):
    """Detailed record of production incidents."""

    task_item_id: int | None = Field(default=None, foreign_key="taskitem.id")
    work_item_id: int | None = Field(default=None, foreign_key="workitem.id")
    node_id: str | None = None
    incident_type: str
    description: str
    reported_by: str
    assigned_group: str | None = Field(
        default=None, index=True
    )  # Maintenance, Supply, Foreman, etc.
    resolved: bool = Field(default=False)
    resolved_by: str | None = None
    resolved_at: datetime.datetime | None = None
    resolution_note: str | None = None
    downtime_minutes: float | None = None
    attachments: str | None = None  # JSON string (list of paths)


class ChatMessageType(StrEnum):
    MESSAGE = "message"
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    ORDER = "order"
    INCIDENT = "incident"
    HANDOVER = "handover"
    REPORT = "report"


class ChatMessage(BaseEntity, table=True):
    """Shared cluster chat message with context references."""

    author: str
    node_id: str
    message_type: ChatMessageType = Field(default=ChatMessageType.MESSAGE)
    content: str

    ref_project_id: int | None = Field(default=None, foreign_key="project.id")
    ref_work_item_id: int | None = Field(default=None, foreign_key="workitem.id")
    ref_task_item_id: int | None = Field(default=None, foreign_key="taskitem.id")

    parent_message_id: int | None = Field(default=None, foreign_key="chatmessage.id")
    template_name: str | None = None
    attachments: str | None = None  # JSON string
    is_read: bool = Field(default=False)


class Tag(BaseEntity, table=True):
    """Visual tags for grouping/flagging entities."""

    name: str = Field(unique=True)
    color: str | None = None
    ref_project_id: int | None = Field(default=None, foreign_key="project.id")
    ref_work_item_id: int | None = Field(default=None, foreign_key="workitem.id")
    ref_task_item_id: int | None = Field(default=None, foreign_key="taskitem.id")


class ReportTemplate(BaseEntity, table=True):
    """Jinja2 HTML templates for the reporting system."""

    name: str
    author: str | None = None
    template_html: str
    description: str | None = None
    last_used_at: datetime.datetime | None = None


class ViewPreset(BaseEntity, table=True):
    """UI configuration presets (Notion-style tabs)."""

    module: str
    owner: str  # username or "global"
    name: str
    preset_json: str  # JSON config
    is_default: bool = Field(default=False)


class NotificationTemplate(BaseEntity, table=True):
    """Configurable notification texts."""

    key: str = Field(unique=True, index=True)
    text: str
    enabled: bool = Field(default=True)
