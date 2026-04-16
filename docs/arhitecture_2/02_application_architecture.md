# DocuFlow — Application Architecture Document

> **Версия:** 2.0 (на основе Master Plan v7)
> **Стек:** Python 3.12 · NiceGUI · SQLModel · SQLite · FileBus (file-based P2P)

---

## 1. Принципы архитектуры

| Принцип | Описание |
|---|---|
| **Vertical Slice** | Каждый модуль = папка `system.py` + `view.py`. Нет shared services кроме core. |
| **Code as Documentation** | Docstrings описывают архитектурные решения, не просто "что делает" |
| **Decentralized** | Каждый узел = автономная единица с локальной БД |
| **Master Election** | Роль мастера динамически выбирается кластером |
| **Immutable Source** | Сетевые файлы читаются, но никогда не изменяются |
| **Local env only** | Пути к дискам — только через .env, никогда не синхронизируются |
| **Idempotent Scan** | Повторный poll не создаёт дублей: upsert по file_path (relative) |
| **Atomic Writes** | Все записи на диск: tmp → fsync → os.replace |

---

## 2. Структура проекта (Vertical Slices)

```
src/docuflow/
│
├── domain/                         # Чистый домен (без зависимостей)
│   ├── entities/
│   │   ├── base.py                 # BaseEntity (id, created_at, updated_at)
│   │   ├── identity.py             # User, Role, Workplace (существует ✅)
│   │   ├── settings.py             # SettingsRegistry, BaseModuleSettings (✅)
│   │   └── production.py           # ♻️ Переписать: все производственные сущности
│   └── ...
│
├── infrastructure/
│   ├── config.py                   # Config (cold boot, из env)
│   ├── database.py                 # SQLite engine, session factory
│   └── file_bus/                   # FileBus P2P протокол (✅)
│
├── application/
│   └── base.py                     # BaseSystem (lifecycle: on_startup/on_shutdown)
│
├── features/                       # Vertical Slices
│   │
│   ├── folder_scanner/             # 📁 Фаза 1
│   │   ├── system.py               # FolderScannerSettings + FolderScannerSystem
│   │   ├── scanner.py              # Polling loop (master only) + filelock
│   │   ├── ns_mirror.py            # NSMirrorService (all nodes, 60s, timeout=30s)
│   │   ├── view.py                 # Статус + лог + Scan Now
│   │   └── parsers/
│   │       ├── gnc.py              # GncParser: *SHEET, Material, PART NAME, estimate_time()
│   │       ├── folder_name.py      # FolderNameParser: SIDRA_REGEX + fallback
│   │       └── task_file.py        # TaskFileParser: is_variant dedup, step/batch_index
│   │
│   ├── work_items/                 # 📋 Фаза 2
│   │   ├── system.py               # WorkItemSystem: CRUD + lifecycle + register_document
│   │   └── view.py                 # Список + карточка + WorkLog + PartTemplate alerts
│   │
│   ├── task_board/                 # 🔧 Фаза 2
│   │   ├── batch_engine.py         # BatchEngine + BatchRule + DEFAULT_RULE
│   │   ├── system.py               # TaskBoardSystem: bucket, status, time tracking, drift%
│   │   └── view.py                 # Оператор: корзина | Бригадир: все узлы
│   │
│   ├── part_library/               # 🔩 Фаза 3
│   │   ├── system.py               # PartLibrarySystem: upsert, find_by_bbox±tol, обратный поиск
│   │   └── view.py                 # Таблица + SVG превью + PartTemplate + bbox range slider
│   │
│   ├── inventory/                 # 🏭 Фаза 3
│   │   ├── system.py               # MaterialSystem + аудит + резервирование
│   │   └── view.py                 # Типы (с time params) + остатки + аудит-лента
│   │
│   ├── consumables/                # 🔩 Фаза 3
│   │   ├── system.py               # ConsumableSystem: use/restock + критический остаток
│   │   └── view.py                 # Список + min_quantity алерт + лог
│   │
│   ├── production/                 # 📦 Фаза 4
│   │   ├── system.py               # ProductionUnit: create/split/merge + generate_human_id
│   │   └── view.py                 # Live search ≥2 символа + карточка + split UI + Explorer
│   │
│   ├── chat/                       # 💬 Фаза 4
│   │   ├── system.py               # ChatSystem: древовидные треды + типы + файлы + шаблоны
│   │   └── view.py                 # ChatPanel + InboxView + compose с вложениями
│   │
│   ├── incidents/                  # ⚠️ Фаза 4
│   │   ├── system.py               # IncidentSystem: report → чат + resolve → downtime stats
│   │   └── view.py                 # Список инцидентов + статистика простоев
│   │
│   ├── reports/                    # 📄 Фаза 5
│   │   ├── system.py               # ReportSystem: ReportRegistry + Jinja2 + weasyprint PDF
│   │   └── view.py                 # Список шаблонов + динамическая форма параметров
│   │
│   ├── analytics/                  # 📊 Фаза 5
│   │   └── view.py                 # KPI карточки + drift% по узлам + незакрытые наряды
│   │
│   └── admin/                      # ⚙️ Существует (доработать)
│       ├── system.py               # + Settings Editor + ViewPreset mgmt + NotificationTemplate
│       └── view.py                 # User/Role/Matrix + Workplace + Settings + Presets
│
├── lib/
│   └── widgets/                    # Переиспользуемые NiceGUI компоненты
│       ├── status_badge.py         # Бейджи всех статусов (WorkItem, TaskItem)
│       ├── work_item_card.py       # Карточка наряда (тип/статус/дата/chat_count)
│       ├── task_item_row.py        # Строка таска (приоритет/материал/прогресс/urgent)
│       ├── material_chip.py        # Чип "AA 5052-H32 / 3mm"
│       ├── part_preview.py         # SVG из SVGGenerator (bbox + превью)
│       ├── scan_log_panel.py       # Лог сканера (live scroll)
│       ├── file_changed_alert.py   # Диалог: GNC изменился — Обновить/Оставить/Напомнить
│       ├── chat_thread.py          # Дерево сообщений (рекурсивный виджет)
│       ├── chat_compose.py         # Composer с типами + шаблоны + вложения
│       ├── bucket_panel.py         # Корзина оператора (батчи → таски)
│       ├── batch_card.py           # Карточка батча с drag&drop
│       ├── report_builder.py       # Конструктор отчётов
│       ├── view_preset_switcher.py # Notion-like вкладки пресетов
│       ├── explorer_button.py      # "📂 Открыть в Explorer" + fallback с текстом пути
│       └── ns_mirror_status.py     # Индикатор синхронизации NS (OK/Pending/Alert)
│
└── sdk.py                          # SDK Facade (точка входа для фич)
```

---

## 3. Доменные сущности и их связи

### 3.1 Производственная иерархия

```
Project
  ├── WorkItem[] (SIDRA / MIHTAV / REWORK)
  │     ├── TaskItem[] (один GNC файл)
  │     │     ├── TaskPart[] (деталь + qty)
  │     │     │     └── PartLibrary (справочник)
  │     │     │           └── PartTemplate[] (предупреждения)
  │     │     ├── ProductionUnit[] (паллета)
  │     │     │     └── StorageLocation
  │     │     ├── WorkLog[]
  │     │     └── WorkerBucketEntry[]
  │     ├── Reservation[] → MaterialStock
  │     └── WorkLog[]
  │
MaterialType (библиотека)
  ├── MaterialStock[] (физические пачки)
  │     ├── Reservation[] (резерв под WI)
  │     └── MaterialAudit[] (движения)
  └── [cut_speed_mm_per_min, pierce_time_sec, idle_speed_mm_per_min, time_tolerance_pct]

Consumable → ConsumableLog[]
IncidentLog → (ref: TaskItem / WorkItem) + attachments (JSON paths)
ChatMessage → (ref: Project / WorkItem / TaskItem)
            → parent_message (дерево ответов)
            → attachments (JSON paths)
Tag → (ref: Project / WorkItem / TaskItem)
ReportTemplate → (Jinja2 HTML, используется ReportSystem)
ViewPreset → (owner: username | "global")
NotificationTemplate → (key → text с {переменными})
```

### 3.2 Ключевые статусы WorkItem

```
         ┌─ PENDING_CUTS (папка без GNC файлов)
         │     → при появлении GNC → автоматически NEW
SCAN ────┤
         └─ NEW (папка + GNC) ─────────────────────┐
                                                    ▼
FOLDER_NO_DOC ←── нет бумаги ──── REGISTERED ──────► IN_PROGRESS
DOC_NO_FOLDER ←── нет папки ──┘                          │
                                                     ON_HOLD ◄───┐
                                              BLOCKED ◄─────┘    │
                                               (запас / раскрой) │
                                                    ▼             │
                                                  DONE ──────────┘
                                               CANCELLED
                                               ARCHIVED
```

### 3.3 Ключевые статусы TaskItem

```
PLANNED → IN_PROGRESS → ON_HOLD (с причиной) → IN_PROGRESS → DONE
                     → BLOCKED (внешняя блокировка бригадиром)
                     → CANCELLED
```

### 3.4 Полный список сущностей БД

| Сущность | Таблица | Описание |
|---|---|---|
| Project | project | Контейнер верхнего уровня |
| WorkItem | workitem | Наряд / письмо / доработка |
| TaskItem | taskitem | Один GNC файл. sheets_done, estimated/actual minutes |
| TaskPart | taskpart | Деталь (SKU + version + version_suffix + qty) в TaskItem |
| PartLibrary | partlibrary | Справочник деталей (SKU → bbox из SVGGenerator) |
| PartTemplate | parttemplate | Шаблон предупреждения для проблемной детали |
| MaterialType | materialtype | Библиотека материалов + time params резки |
| MaterialStock | materialstock | Физическая пачка на складе |
| Reservation | reservation | Soft/Hard резерв материала под WorkItem |
| MaterialAudit | materialaudit | Движения материала |
| Consumable | consumable | Расходник (сопла, линзы, лента...) |
| ConsumableLog | consumablelog | Движения расходников |
| StorageLocation | storagelocation | Место складирования (стеллаж) |
| ProductionUnit | productionunit | Паллета. label_id="25-07-А-042". Split/merge |
| WorkerBucketEntry | workerbucketentry | Корзина оператора. Handover поддержка |
| WorkLog | worklog | Журнал трассировки всех событий |
| IncidentLog | incidentlog | Инциденты + вложения (JSON paths) |
| ChatMessage | chatmessage | Чат (дерево ответов + типы + вложения) |
| Tag | tag | Тег (Срочно/Внимание/Брак) |
| ReportTemplate | reporttemplate | Шаблон отчёта (Jinja2 HTML) |
| ViewPreset | viewpreset | Notion-подобный пресет вида |
| NotificationTemplate | notificationtemplate | Настраиваемые тексты уведомлений |

---

## 4. Системные компоненты

### 4.1 BaseSystem (lifecycle)

```python
class BaseSystem:
    def __init__(self, config: Config): ...
    async def on_startup(self) -> None: ...   # инициализация
    async def on_shutdown(self) -> None: ...  # завершение
```

Все системы (FolderScannerSystem, WorkItemSystem, ...) наследуют BaseSystem.

### 4.2 BaseModuleSettings

```python
class BaseModuleSettings(BaseModel):
    # scope="local"  → из .env, не синхронизируется
    # scope="global" → в БД, синхронизируется через FileBus snapshot
```

Декларативная система настроек. Регистрируется в SettingsRegistry.

### 4.3 FileBus (P2P протокол)

```
REQ_{from}_{to}_{id}.json → обработчик → RES_{from}_{to}_{id}.json
BROADCAST_{from}_{id}.json → все узлы читают + удаляют после обработки

Команды (ключевые):
  lock_batch         → мастер резервирует TaskItem за узлом (WorkerBucketEntry)
  file_changed       → broadcast при изменении GNC хэша
  ns_mirror_alert    → broadcast при расхождении NS/сеть
  snapshot_sync      → полная синхронизация БД
```

### 4.4 FolderScanner (master-only)

```python
# Файловая блокировка — защита от конкурентного сканирования
lock_path = Path(settings.sidra_scan_path) / ".docuflow.lock"
with filelock.FileLock(str(lock_path), timeout=5):
    scan_folder(...)

# Алгоритм:
async polling loop (master):
  FOR path IN [sidra_path, mihtav_path, other_path]:
    FOR folder IN path.iterdir():
      gnc_files = [f for f in folder if f.suffix == ".GNC"
                                    and not is_variant(f)]

      IF gnc_files == []:
        → WorkItem(PENDING_CUTS) + notify(template="scan.empty_folder")
      ELSE:
        work_item = upsert_work_item(folder)   # идемпотентно по folder_name
        FOR gnc IN gnc_files:
          task = upsert_task_item(gnc, work_item)  # идемпотентно по file_path (relative)
          IF hash_changed(task, gnc):
            → WorkLog(FILE_CHANGED) + broadcast(FILE_CHANGED_ALERT)
            → atomic_write если нужно обновить локальный файл
          parse_gnc(gnc) → mat_type + task_parts + part_library
          svg_gen.generate_thumbnail(part) → bbox_x, bbox_y  # НЕ PART SIZE!
```

### 4.5 NSMirrorService (all nodes)

```python
# На каждом узле — свой экземпляр
background loop (check_interval=60s, copy_timeout=30s):
  FOR entry IN WorkerBucket[this_node]:
    network_file = scan_root / entry.task_item.file_path   # relative path!
    local_file   = ns_folder / entry.task_item.file_name

    IF not local_file.exists():
      copy(network_file → local_file, timeout=30s)
      WorkLog(NS_MIRROR, "Скопирован в NS")

    ELIF md5(network_file) != md5(local_file):
      WorkLog(FILE_CHANGED, "Сетевой файл изменился!")
      alert_operator(dialog: "Обновить NS / Оставить / Напомнить позже")

  ON entry removed from bucket:
    delete(local_file)
    WorkLog(NS_MIRROR, "Удалён из NS")
```

### 4.6 BatchEngine

```python
# Стандартное правило (DEFAULT_RULE):
DEFAULT_RULE = BatchRule(
    name="Standard",
    match_same_material=True,
    match_same_thickness=True,
    match_same_sheet_size=True,
    match_same_project=False,   # из разных нарядов — допустимо
    max_items_per_batch=10,
)

# Алгоритм:
BatchEngine.compute(tasks[], rule) → batches[]:
  GROUP BY: mat_type_id + thickness + sheet_x + sheet_y (+ project если нужно)
  per batch: batch_group_id = uuid4()

# Рекомендации при редактировании батча:
  → TaskItem из других нарядов с совпадающим MAT (предложить добавить)
  → STOCK_ALERT если task_parts содержат детали из is_stock=True ProductionUnit
```

### 4.7 Временные оценки (TaskItem)

```python
# Параметры в MaterialType (редактируются бригадиром):
#   cut_speed_mm_per_min, pierce_time_sec, idle_speed_mm_per_min, time_tolerance_pct

def estimate_time(gnc_sheet, mat_type) -> int:  # минуты
    pierce = contour_count * mat_type.pierce_time_sec
    cut    = cut_length_mm / mat_type.cut_speed_mm_per_min * 60
    idle   = idle_length_mm / mat_type.idle_speed_mm_per_min * 60
    base   = (pierce + cut + idle) * sheet_qty / 60
    return int(base * (1 + mat_type.time_tolerance_pct / 100))

# Фактическое время:
actual_minutes = (completed_at - started_at) - Σ(on_hold durations)
drift_pct = (actual - estimated) / estimated * 100

# Бригадир корректирует time_tolerance_pct / cut_speed при систематическом дрейфе
```

### 4.8 ReportSystem (модульный)

```python
# Каждый модуль регистрирует блоки при on_startup:
class ReportDataBlock:
    name: str           # "work_items_summary"
    params: list[str]   # ["date_from", "date_to", "node_id"]
    query_fn: callable

# Зарегистрированные блоки:
#   work_items:  "work_items_summary", "work_item_detail"
#   task_board:  "tasks_by_node", "shift_completion"
#   material:    "material_usage", "stock_snapshot"
#   incidents:   "incident_log", "downtime_summary"
#   part_lib:    "parts_produced"

def generate(template: ReportTemplate, params: dict) -> bytes:
    context = {"blocks": BlockProxy(registry, params), "params": params}
    html = jinja2_env.render(template.template_html, context)
    pdf  = weasyprint.HTML(string=html).write_pdf()
    return pdf   # → ui.download()
```

### 4.9 Поиск деталей

```sql
-- Прямой: деталь X в наряде Y
SELECT wi.folder_name, ti.file_name, tp.qty
FROM taskpart tp
JOIN taskitem ti ON tp.task_item_id = ti.id
JOIN workitem wi ON ti.work_item_id = wi.id
WHERE tp.part_sku = :sku AND wi.folder_name = :folder_name

-- Обратный: все наряды/проекты с деталью X
SELECT DISTINCT p.name, wi.folder_name, wi.status
FROM taskpart tp
JOIN taskitem ti ON tp.task_item_id = ti.id
JOIN workitem wi ON ti.work_item_id = wi.id
JOIN project p   ON wi.project_id = p.id
WHERE tp.part_sku = :sku

-- По габаритам с допуском:
SELECT sku, bbox_x, bbox_y, hole_count
FROM partlibrary
WHERE bbox_x BETWEEN :x_min AND :x_max
AND   bbox_y BETWEEN :y_min AND :y_max
[AND  mat_type_id = :type]
[AND  hole_count = :holes]
[AND  corner_count BETWEEN :min AND :max]

-- Паллеты с деталью X:
SELECT pu.label_id, sl.code, pu.qty_produced, pu.is_stock
FROM productionunit pu
JOIN taskitem ti ON pu.task_item_id = ti.id
JOIN taskpart tp ON tp.task_item_id = ti.id
LEFT JOIN storagelocation sl ON pu.storage_location_id = sl.id
WHERE tp.part_sku = :sku
```

---

## 5. Конфигурация

### 5.1 Cold config (.env — LOCAL, не синхронизируется)

```env
# Идентификация узла
DOCUFLOW_NODE_ID=LASER_1
DOCUFLOW_NODE_CODE=А          # Короткий код для label_id паллеты ("25-07-А-042")

# Пути к сетевым папкам (буква диска своя на каждом ПК)
DOCUFLOW_FOLDER_SCANNER__SIDRA_SCAN_PATH=Z:\sidra
DOCUFLOW_FOLDER_SCANNER__MIHTAV_SCAN_PATH=Z:\mihtav
DOCUFLOW_FOLDER_SCANNER__OTHER_SCAN_PATH=Z:\other
DOCUFLOW_FOLDER_SCANNER__LOCAL_NS_PATH=C:\NS\cutting

# NS Mirror параметры
DOCUFLOW_FOLDER_SCANNER__NS_MIRROR_INTERVAL_SECONDS=60
DOCUFLOW_FOLDER_SCANNER__NS_MIRROR_COPY_TIMEOUT_S=30

# Polling
DOCUFLOW_FOLDER_SCANNER__POLL_INTERVAL_SECONDS=300
```

### 5.2 Runtime settings (GLOBAL — в БД, синхр. через snapshot)

```python
class FolderScannerSettings(BaseModuleSettings):
    # LOCAL — env per node, НИКОГДА не синхронизируются через P2P
    sidra_scan_path: str = Field(default="", json_schema_extra={"scope": "local"})
    mihtav_scan_path: str = Field(default="", json_schema_extra={"scope": "local"})
    other_scan_path: str = Field(default="", json_schema_extra={"scope": "local"})
    poll_interval_seconds: int = Field(default=300, json_schema_extra={"scope": "local"})

    # GLOBAL — синхронизируются через P2P
    enabled: bool = Field(default=True, json_schema_extra={"scope": "global"})
    default_project_name: str = Field(default="Default", json_schema_extra={"scope": "global"})
```

---

## 6. UI архитектура (NiceGUI)

### 6.1 Структура портала

```
┌──────────────────────────────────────────────────────┐
│  [STATUS BAR]  Кто мастер? Узел? NS статус? Алерты?  │
├──────────────────────────────────────────────────────┤
│  [LEFT NAV]    Модули (фильтруются по Role.modules)  │
├──────────────────────────────────────────────────────┤
│  [MAIN AREA]   Активный View модуля                   │
│                ┌──────────────────────────────────┐   │
│                │  ViewPreset tabs (Notion-style)   │   │
│                ├──────────────────────────────────┤   │
│                │  Content (table/kanban/cards)     │   │
│                └──────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### 6.2 Адаптивность по ролям

```python
# Навигация строится из пересечения:
user_modules = set(role.allowed_modules for role in user.roles)
workplace_modules = set(workplace.allowed_modules)
visible = user_modules ∩ workplace_modules
```

### 6.3 ViewPreset система

```
Каждый модуль имеет именованные пресеты:
  preset_json: { filters, sort, group_by, columns, view_type }
  view_type: "table" | "kanban" | "list" | "cards"

Личные: owner = username
Общие:  owner = "global" (создаёт бригадир/начальник)
UI: вкладки переключателя вверху таблицы (как в Notion)
```

### 6.4 NotificationTemplate

```
NotificationTemplate:
  key: str       # "scan.empty_folder", "scan.new_work_item", "stock.alert"
  text: str      # Шаблон: "⚠️ {folder_name}: нестов нет!"
  enabled: bool

render_template(key, {folder_name=...}) → итоговый текст
Управляется через Admin Panel (CRUD)
```
