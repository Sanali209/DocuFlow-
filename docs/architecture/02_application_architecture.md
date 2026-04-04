# DocuFlow — Application Architecture Document

> **Версия:** 1.0
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
│   │   ├── scanner.py              # Polling loop (master only)
│   │   ├── ns_mirror.py            # NSMirrorService (all nodes)
│   │   ├── view.py                 # Статус + лог + Scan Now
│   │   └── parsers/
│   │       ├── gnc.py              # GncParser (адаптирован из MVP)
│   │       ├── folder_name.py      # FolderNameParser (SIDRA regex + fallback)
│   │       └── task_file.py        # TaskFileParser (is_variant dedup)
│   │
│   ├── work_items/                 # 📋 Фаза 2
│   │   ├── system.py               # WorkItemSystem (CRUD + lifecycle)
│   │   └── view.py                 # Список + карточка + WorkLog
│   │
│   ├── task_board/                 # 🔧 Фаза 2
│   │   ├── batch_engine.py         # BatchEngine + BatchRule
│   │   ├── system.py               # TaskBoardSystem (bucket, status)
│   │   └── view.py                 # Оператор / Бригадир views
│   │
│   ├── part_library/               # 🔩 Фаза 3
│   │   ├── system.py               # PartLibrarySystem (поиск + SVG)
│   │   └── view.py
│   │
│   ├── material_stock/             # 🏭 Фаза 3
│   │   ├── system.py
│   │   └── view.py
│   │
│   ├── consumables/                # 🔩 Фаза 3
│   │   ├── system.py
│   │   └── view.py
│   │
│   ├── production/                 # 📦 Фаза 4
│   │   ├── system.py               # ProductionUnit create/split/merge
│   │   └── view.py
│   │
│   ├── chat/                       # 💬 Фаза 4
│   │   ├── system.py               # ChatSystem (древовидные треды)
│   │   └── view.py
│   │
│   ├── incidents/                  # ⚠️ Фаза 4
│   │   ├── system.py
│   │   └── view.py
│   │
│   ├── reports/                    # 📄 Фаза 5
│   │   ├── system.py               # ReportSystem (Jinja2 + PDF)
│   │   └── view.py
│   │
│   ├── analytics/                  # 📊 Фаза 5
│   │   └── view.py
│   │
│   └── admin/                      # ⚙️ Существует (доработать)
│       ├── system.py
│       └── view.py
│
├── lib/
│   └── widgets/                    # Переиспользуемые NiceGUI компоненты
│       ├── status_badge.py
│       ├── work_item_card.py
│       ├── task_item_row.py
│       ├── material_chip.py
│       ├── part_preview.py         # SVG из SVGGenerator
│       ├── scan_log_panel.py
│       ├── file_changed_alert.py
│       ├── chat_thread.py
│       ├── chat_compose.py
│       ├── bucket_panel.py
│       ├── batch_card.py
│       ├── report_builder.py
│       ├── view_preset_switcher.py
│       ├── explorer_button.py      # subprocess → explorer.exe
│       └── ns_mirror_status.py     # Индикатор синхронизации NS
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
  └── [cut_speed, pierce_time, idle_speed, tolerance%]

Consumable → ConsumableLog[]
IncidentLog → (ref: TaskItem / WorkItem)
ChatMessage → (ref: Project / WorkItem / TaskItem)
            → parent_message (дерево)
Tag → (ref: Project / WorkItem / TaskItem)
ReportTemplate → (используется ReportSystem)
ViewPreset → (owner: user или "global")
NotificationTemplate → (key → text с переменными)
```

### 3.2 Ключевые статусы WorkItem

```
         ┌─ PENDING_CUTS (папка без GNC файлов)
SCAN ────┤
         └─ NEW (папка + GNC) ──────────────────┐
                                                 ▼
FOLDER_NO_DOC ←── нет бумаги ──── REGISTERED ──────► IN_PROGRESS
DOC_NO_FOLDER ←── нет папки ──┘                            │
                                                       ON_HOLD
                                              BLOCKED ◄─────┘
                                                     (запас/раскрой)
                                                ▼
                                              DONE → ARCHIVED
                                           CANCELLED
```

### 3.3 Полный список сущностей БД

| Сущность | Таблица | Описание |
|---|---|---|
| Project | project | Контейнер верхнего уровня |
| WorkItem | workitem | Наряд / письмо / доработка |
| TaskItem | taskitem | Один GNC файл |
| TaskPart | taskpart | Деталь в TaskItem |
| PartLibrary | partlibrary | Справочник деталей (SKU → bbox) |
| PartTemplate | parttemplate | Шаблон предупреждения для детали |
| MaterialType | materialtype | Библиотека материалов |
| MaterialStock | materialstock | Физическая пачка на складе |
| Reservation | reservation | Резерв материала |
| MaterialAudit | materialaudit | Движения материала |
| Consumable | consumable | Расходник |
| ConsumableLog | consumablelog | Движения расходников |
| StorageLocation | storagelocation | Место складирования |
| ProductionUnit | productionunit | Паллета с деталями |
| WorkerBucketEntry | workerbucketentry | Запись в корзине оператора |
| WorkLog | worklog | Журнал трассировки |
| IncidentLog | incidentlog | Инциденты |
| ChatMessage | chatmessage | Сообщение чата (дерево) |
| Tag | tag | Тег (Срочно/Внимание/Брак) |
| ReportTemplate | reporttemplate | Шаблон отчёта (Jinja2 HTML) |
| ViewPreset | viewpreset | Пресет вида (Notion-подобный) |
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
BROADCAST_{from}_{id}.json → все узлы читают

Команды (ключевые):
  lock_batch      → мастер резервирует TaskItem за узлом
  file_changed    → broadcast при изменении GNC хэша
  ns_mirror_alert → broadcast при расхождении NS/сеть
  snapshot_sync   → полная синхронизация БД
```

### 4.4 FolderScanner (master-only)

```
async polling loop (master):
  FOR path IN [sidra_path, mihtav_path, other_path]:
    FOR folder IN path.iterdir():
      gnc_files = [f for f in folder if f.suffix == ".GNC"
                                    and not is_variant(f)]

      IF gnc_files == []:
        → WorkItem(PENDING_CUTS) + notify(template="scan.empty_folder")
      ELSE:
        work_item = upsert_work_item(folder)
        FOR gnc IN gnc_files:
          task = upsert_task_item(gnc, work_item)
          IF hash_changed(task, gnc):
            → WorkLog(FILE_CHANGED) + broadcast(FILE_CHANGED_ALERT)
          parse_gnc(gnc) → mat_type + task_parts + part_library
```

### 4.5 NSMirrorService (all nodes)

```
background loop (check_interval=60s):
  FOR entry IN WorkerBucket[this_node]:
    network_file = scan_root / entry.task_item.file_path
    local_file   = ns_folder / entry.task_item.file_name
    
    copy_if_missing(network_file → local_file, timeout=30s)
    alert_if_changed(network_file, local_file)
  
  on_bucket_remove(entry):
    delete(local_file)
```

### 4.6 BatchEngine

```
BatchRule → criteria: MAT + THK + SIZE + (optional) project
BatchEngine.compute(tasks[], rule) → batches[] with batch_group_id (UUID)

Рекомендации:
  → TaskItem из других нарядов с совпадающим MAT (можно добавить в батч)
  → STOCK_ALERT если task_parts содержат детали из is_stock=True ProductionUnit
```

### 4.7 ReportSystem (модульный)

```
ReportDataBlock: name, params[], query_fn
ReportRegistry:  register(block) / get_block(name) / available_blocks()

Каждый модуль регистрирует блоки при on_startup:
  work_items → "work_items_summary", "work_item_detail"
  task_board → "tasks_by_node", "shift_completion"
  material   → "material_usage", "stock_snapshot"
  incidents  → "incident_log", "downtime_summary"
  part_lib   → "parts_produced"

generate(template, params):
  context = { blocks: BlockProxy(registry, params), params }
  html = jinja2.render(template.html, context)
  pdf  = weasyprint.render(html)
  → ui.download(pdf)
```

---

## 5. Конфигурация

### 5.1 Cold config (.env — LOCAL, не синхронизируется)

```env
# Идентификация узла
DOCUFLOW_NODE_ID=LASER_1
DOCUFLOW_NODE_CODE=А          # Короткий код для label_id паллеты

# Пути к сетевым папкам (буква диска своя на каждом ПК)
DOCUFLOW_FOLDER_SCANNER__SIDRA_SCAN_PATH=Z:\sidra
DOCUFLOW_FOLDER_SCANNER__MIHTAV_SCAN_PATH=Z:\mihtav
DOCUFLOW_FOLDER_SCANNER__OTHER_SCAN_PATH=Z:\other
DOCUFLOW_FOLDER_SCANNER__LOCAL_NS_PATH=C:\NS\cutting

# NS Mirror интервалы
DOCUFLOW_FOLDER_SCANNER__NS_MIRROR_INTERVAL_SECONDS=60
DOCUFLOW_FOLDER_SCANNER__NS_MIRROR_COPY_TIMEOUT_S=30
```

### 5.2 Runtime settings (GLOBAL — в БД, синхр. через snapshot)

```python
class FolderScannerSettings(BaseModuleSettings):
    enabled: bool = True                         # scope="global"
    default_project_name: str = "Default"        # scope="global"
    poll_interval_seconds: int = 300             # scope="local"
```

---

## 6. UI архитектура (NiceGUI)

### 6.1 Структура портала

```
┌──────────────────────────────────────────────────────┐
│  [STATUS BAR]  Кто мастер? Узел? Алерты?             │
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
Каждый modules имеет именованные пресеты:
  preset_json: { filters, sort, group_by, columns, view_type }
  view_type: "table" | "kanban" | "list" | "cards"

Личные: owner = username
Общие:  owner = "global" (создаёт бригадир/начальник)
UI: вкладки переключателя вверху таблицы
```
