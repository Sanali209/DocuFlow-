# DF-001: Доменные сущности (production.py)

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 — Домен + FolderScanner |
| **Priority** | 🔴 CRITICAL |
| **Status** | TODO |
| **Зависит от** | *(нет — первый тикет)* |
| **Блокирует** | DF-002, DF-003, DF-004, DF-005, DF-006, DF-007, DF-008, все остальные |
| **Архитектура** | [02_application_architecture.md §3](../architecture/02_application_architecture.md) |
| **Data Flow** | [03_data_flow.md §2](../architecture/03_data_flow.md) |

---

## Контекст

Текущий `domain/entities/production.py` устарел — содержит сущности из старого MVP. Все дальнейшие модули зависят от единой, корректной доменной модели.

Это **фундамент всей системы**. Ошибка здесь обойдётся дорого при исправлении.

---

## Цель

Переписать `src/docuflow/domain/entities/production.py` содержащий **все** SQLModel сущности производственного домена.

---

## Execution Plan

```
1. Изучить BaseEntity из base.py (id, created_at, updated_at — уже есть)
2. Изучить текущий production.py — что можно сохранить
3. Написать тесты ПЕРВЫМИ (TDD)
4. Реализовать сущности блоками, в правильном порядке зависимостей:
   Block A: Project, WorkItem, TaskItem, TaskPart, PartLibrary, PartTemplate
   Block B: MaterialType, MaterialStock, Reservation, MaterialAudit
   Block C: Consumable, ConsumableLog
   Block D: StorageLocation, ProductionUnit
   Block E: WorkerBucketEntry, WorkLog, IncidentLog
   Block F: ChatMessage, Tag, ReportTemplate, ViewPreset, NotificationTemplate
5. Проверить миграции (create_all при старте)
6. Убедиться что все импорты в sdk.py корректны
```

---

## Подзадачи

### A. Проекты и Наряды
- [x] `Project` (id, name unique idx, description, is_default, deadline, status enum)
- [x] `WorkItemType` enum: `SIDRA | MIHTAV | REWORK`
- [x] `WorkItemStatus` enum:
  - `NEW` — сканер нашёл папку + GNC
  - `PENDING_CUTS` — папка без GNC (ждём раскрой)
  - `FOLDER_NO_DOC` — GNC есть, бумаги нет
  - `DOC_NO_FOLDER` — бумага есть, папки нет
  - `REGISTERED` — папка + документ подтверждены
  - `IN_PROGRESS` — хотя бы 1 TaskItem in_progress
  - `ON_HOLD` — приостановлено (причина в WorkLog)
  - `BLOCKED` — ждём переделки нестов
  - `DONE` — все TaskItem done
  - `CANCELLED` — отменён
  - `ARCHIVED` — в архиве
- [x] `WorkItem` (project_id FK, type, status, folder_name unique idx, folder_path relative, sidra_number?, sidra_step?, folder_found_at, doc_received_at?, started_at?, completed_at?, last_scanned_at?)

### B. Задачи (Несты)
- [x] `TaskItemStatus` enum: `PLANNED | IN_PROGRESS | ON_HOLD | DONE | CANCELLED | BLOCKED`
- [x] `TaskItem`:
  - work_item_id FK, mat_type_id? FK
  - status, priority 0-2, is_urgent bool
  - file_name, file_path (RELATIVE!), file_hash MD5
  - sheet_x?, sheet_y?, sheet_qty?, thickness?, gnc_date?
  - sheets_done int=0, qty_produced? int
  - estimated_minutes? int, actual_minutes? int
  - step_index?, batch_index?
  - assigned_to_node?, scanned_at, started_at?, completed_at?
  - block_reason? str
- [x] `TaskPart` (task_item_id FK, part_sku FK, version str, qty int)

### C. Библиотека деталей
- [x] `PartLibrary` (sku PK idx, mat_type_id? FK, name?, bbox_x?, bbox_y?, contour_count, corner_count, hole_count, weight_per_pcs?, svg_preview_path?, first_seen_at, last_seen_at)
- [x] `PartTemplate` (id, part_sku FK, message, severity: info|warning|critical, created_by)

### D. Материалы
- [x] `MaterialFormFactor` enum: `SHEET | TUBE | BAR | OTHER`
- [x] `MaterialType` (code idx, form_factor, thickness?, nominal_x?, nominal_y?, weight_per_sheet?, primary_unit, **cut_speed_mm_per_min, pierce_time_sec, idle_speed_mm_per_min, time_tolerance_pct=15**)
- [x] `MaterialStockStatus` enum: `AVAILABLE | RESERVED | ALLOCATED | CONSUMED | DEFECT`
- [x] `MaterialStock` (mat_type_id FK, status, batch_code?, quantity, quantity_kg?, location?)
- [x] `Reservation` (stock_item_id FK, work_item_id FK, qty_reserved, reservation_type: soft|hard)
- [x] `MaterialAudit` (stock_item_id FK, operation: income|write_off|correction|defect|reorder, qty_delta, qty_kg_delta?, reason?, ref_task_item_id?, author?, node_id?)

### E. Расходники
- [x] `Consumable` (name unique idx, category: nozzle|lens|tape|gas|other, unit, quantity, min_quantity)
- [x] `ConsumableLog` (consumable_id FK, operation: use|restock|write_off, qty_delta, ref_task_item_id?, author?, note?)

### F. Производственная логистика
- [x] `StorageLocation` (code unique idx, name?, is_active bool)
- [x] `ProductionUnit`:
  - label_id unique idx (human-readable "25-07-А-042")
  - task_item_id? FK (NULL для до-системных паллет)
  - storage_location_id? FK
  - qty_produced int
  - is_stock bool=False
  - is_pre_system bool=False
  - stock_transferred_at?
  - parent_label_id? str (если создана split-ом)
  - created_by? str

### G. Корзина оператора
- [x] `WorkerBucketEntry` (node_id idx, assigned_user?, task_item_id FK, batch_group_id? UUID, locked_at, handover_note?, handover_at?, handover_from?)

### H. Логи и коммуникация
- [x] `WorkLogType` enum: `INFO | WARNING | FILE_CHANGED | STATUS_CHANGE | ON_HOLD | HANDOVER | STOCK_ALERT | SCAN_ERROR | BLOCKED | EMPTY_FOLDER | NS_MIRROR`
- [x] `WorkLog` (work_item_id? FK, task_item_id? FK, log_type, author?, node_id?, message, payload? JSON str)
- [x] `IncidentLog` (task_item_id? FK, work_item_id? FK, node_id?, incident_type, description, reported_by, resolved bool, resolved_by?, resolved_at?, attachments? JSON)
- [x] `ChatMessageType` enum: `MESSAGE | INFO | WARNING | URGENT | ORDER | INCIDENT | HANDOVER | REPORT`
- [x] `ChatMessage` (author, node_id, message_type, content, ref_project_id? FK, ref_work_item_id? FK, ref_task_item_id? FK, parent_message_id? FK self, template_name?, attachments? JSON, is_read bool)
- [x] `Tag` (name unique, color?, ref_project_id? FK, ref_work_item_id? FK, ref_task_item_id? FK)
- [x] `ReportTemplate` (name, author, template_html str, description?, last_used_at?)
- [x] `ViewPreset` (module str, owner str, name str, preset_json JSON, is_default bool)
- [x] `NotificationTemplate` (key unique idx, text str, enabled bool)

---

## Псевдокод (ключевые паттерны)

```python
# Все сущности наследуют BaseEntity
class WorkItem(BaseEntity, table=True):
    __tablename__ = "workitem"
    
    project_id: int = Field(foreign_key="project.id", index=True)
    work_item_type: WorkItemType
    status: WorkItemStatus = WorkItemStatus.NEW
    
    folder_name: str = Field(unique=True, index=True)  # ключ идемпотентности!
    folder_path: str   # ТОЛЬКО ОТНОСИТЕЛЬНЫЙ путь от scan_root
    
    sidra_number: Optional[str] = None  # nullable — graceful fallback
    sidra_step:   Optional[str] = None  # nullable

    # Все temporal поля — Optional
    folder_found_at: datetime = Field(default_factory=datetime.now)
    doc_received_at: Optional[datetime] = None
    ...

# Временные параметры материала — хранятся в MaterialType
class MaterialType(BaseEntity, table=True):
    ...
    # Параметры для estimate_time() — редактируются бригадиром
    cut_speed_mm_per_min: float = Field(default=3000.0)
    pierce_time_sec:      float = Field(default=3.0)
    idle_speed_mm_per_min:float = Field(default=10000.0)
    time_tolerance_pct:   float = Field(default=15.0)

# ProductionUnit поддерживает split
class ProductionUnit(BaseEntity, table=True):
    task_item_id: Optional[int] = Field(default=None, ...)  # NULL для до-системных
    is_pre_system: bool = Field(default=False)
    parent_label_id: Optional[str] = None  # трассировка split
```

---

## TDD: Тесты написать ПЕРВЫМИ

Файл: `tests/unit/domain/test_production_entities.py`

```python
# --- ТЕСТ 1: WorkItemStatus покрывает все кейсы ---
def test_work_item_status_pending_cuts():
    """Статус PENDING_CUTS существует и отличается от NEW."""
    assert WorkItemStatus.PENDING_CUTS != WorkItemStatus.NEW
    assert WorkItemStatus.PENDING_CUTS.value == "pending_cuts"

# --- ТЕСТ 2: TaskItem.file_path всегда относительный ---
def test_task_item_relative_path():
    """file_path не должен начинаться с буквы диска."""
    task = TaskItem(file_path="sidra\\SIDRA-353203\\01-01-...-ST37.GNC", ...)
    assert not task.file_path.startswith("Z:")
    assert not task.file_path.startswith("C:")

# --- ТЕСТ 3: ProductionUnit поддерживает до-системные паллеты ---
def test_production_unit_pre_system():
    """task_item_id может быть NULL для до-системных паллет."""
    unit = ProductionUnit(label_id="25-07-А-001", task_item_id=None,
                          is_pre_system=True, qty_produced=50)
    assert unit.task_item_id is None
    assert unit.is_pre_system is True

# --- ТЕСТ 4: MaterialType имеет time params ---
def test_material_type_time_params():
    mat = MaterialType(code="AA 5052-H32", thickness=3.0)
    assert mat.cut_speed_mm_per_min == 3000.0  # default
    assert mat.time_tolerance_pct == 15.0

# --- ТЕСТ 5: ChatMessage поддерживает дерево ---
def test_chat_message_tree():
    """parent_message_id — self-referential FK."""
    parent = ChatMessage(id=1, author="user1", ...)
    child  = ChatMessage(id=2, author="user2", parent_message_id=1, ...)
    assert child.parent_message_id == parent.id
```

---

## Definition of Done (Gate)

```
✓ Все сущности из подзадач A-H реализованы в production.py
✓ Все Enum-ы корректны (WorkItemStatus включает PENDING_CUTS + CANCELLED)
✓ SQLite create_all проходит без ошибок
✓ Все unit тесты проходят (pytest tests/unit/domain/)
✓ BaseEntity поля (id, created_at) наследуются корректно
✓ Нет абсолютных путей в сущностях (только file_path как relative str)
✓ task_item_id в ProductionUnit — Optional[int] (nullable)
✓ MaterialType содержит time params с дефолтами
✓ NotificationTemplate сущность создана
```
