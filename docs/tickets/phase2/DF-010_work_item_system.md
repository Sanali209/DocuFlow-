# DF-010: WorkItemSystem

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 2 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md), [DF-006](../phase1/DF-006_folder_scanner_system.md) |
| **Блокирует** | [DF-011](./DF-011_work_items_view.md), [DF-013](./DF-013_task_board_system.md) |
| **Архитектура** | [02_application_architecture.md](../architecture/02_application_architecture.md) |

---

## Контекст

WorkItemSystem управляет жизненным циклом нарядов: CRUD, регистрация бумажных документов, смена статусов, поиск. Бригадир работает с этой системой напрямую.

## Архитектурный контекст

### Место в системе
WorkItemSystem реализуется как вертикальный слайс в `features/work_items/` и наследует `BaseSystem` для управления жизненным циклом.

### Связи с другими системами
| Система | Тип связи | Описание |
|---------|-----------|----------|
| **FolderScanner** | Создание | Автоматически создаёт WorkItem при сканировании папок |
| **TaskBoardSystem** | Потребитель | Использует WorkItem для управления задачами операторов |
| **ReportSystem** | Потребитель | Генерирует отчёты по данным WorkItem |
| **MaterialStock** | Связь | Резервирование материалов для WorkItem |
| **ChatSystem** | Ссылка | Сообщения могут ссылаться на WorkItem |

### Интеграция с FolderScanner
```python
# В folder_scanner/scanner.py (master-only loop)
if gnc_files == []:
    → WorkItem(status=PENDING_CUTS) + notify(template="scan.empty_folder")
else:
    work_item = upsert_work_item(folder)  # → WorkItemSystem.create()
    FOR gnc IN gnc_files:
        task = upsert_task_item(gnc, work_item)
```

### Диаграмма статусов WorkItem

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

### Доменная модель (фрагмент)
```
Project
  ├── WorkItem[] (SIDRA / MIHTAV / REWORK)
  │     ├── TaskItem[] (один GNC файл)
  │     │     ├── TaskPart[] (деталь + qty)
  │     │     ├── ProductionUnit[] (паллета)
  │     │     └── WorkLog[]
  │     ├── Reservation[] → MaterialStock
  │     └── WorkLog[]
```

---

## Execution Plan

```
1. Создать WorkItemSystem(BaseSystem)
2. Реализовать CRUD (create, get, list, update, delete)
3. Реализовать lifecycle методы (register_document, set_status)
4. Реализовать поиск (search + filter)
5. Тесты с in-memory SQLite
```

---

## Подзадачи

- [ ] `WorkItemSystem(BaseSystem)`:
  - [ ] `create(folder_name, work_item_type, project_id?, ...) -> WorkItem`
    - Автоматически определяет Project: по project_hint или default
  - [ ] `get(work_item_id) -> WorkItem`
  - [ ] `list(filters: WorkItemFilters) -> list[WorkItem]`
    - Фильтры: status[], type[], project_id, date_from, date_to, search_text
  - [ ] `register_document(work_item_id, user) -> WorkItem`:
    - `doc_received_at = now()`
    - Переходы статуса:
      - `PENDING_CUTS` → `REGISTERED` (GNC есть)
      - `NEW` → `REGISTERED`
      - `DOC_NO_FOLDER` → остаётся (папки нет)
    - `WorkLog(STATUS_CHANGE, "Документ зарегистрирован {user}")`
  - [ ] `set_status(work_item_id, new_status, reason?, user) -> WorkItem`:
    - Проверка допустимого перехода
    - `WorkLog(STATUS_CHANGE, ...)`
  - [ ] `search(query: str) -> list[WorkItem]`:
    - По: folder_name (partial), sidra_number, project name
  - [ ] `open_in_explorer(work_item_id, node_id)`:
    - Resolve abs path = `scan_root / work_item.folder_path`
    - `subprocess.run(["explorer.exe", abs_path])`
    - Fallback: UNC path если env не настроен

---

## API Спецификация

### Методы WorkItemSystem

#### `create(folder_name: str, work_item_type: WorkItemType, project_id: Optional[int] = None, **kwargs) -> WorkItem`
Создаёт новый WorkItem.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `folder_name` | `str` | Да | Имя папки (например, "SIDRA-353203-SHLAV-2") |
| `work_item_type` | `WorkItemType` | Да | Тип: SIDRA, MIHTAV, REWORK |
| `project_id` | `Optional[int]` | Нет | ID проекта. Если не указан — определяется автоматически |
| `**kwargs` | - | Нет | Дополнительные поля: `sidra_number`, `description`, etc. |

**Возвращает:** `WorkItem` — созданная сущность

**Исключения:**
- `ValueError` — если `project_id` не существует
- `IntegrityError` — если нарушены ограничения уникальности

---

#### `get(work_item_id: int) -> WorkItem`
Получает WorkItem по ID.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `work_item_id` | `int` | Да | ID рабочего элемента |

**Возвращает:** `WorkItem`

**Исключения:**
- `NotFoundError` — если WorkItem не найден

---

#### `list(filters: WorkItemFilters) -> list[WorkItem]`
Возвращает список WorkItem с фильтрацией.

**Структура `WorkItemFilters`:**
```python
class WorkItemFilters(BaseModel):
    status: Optional[list[WorkItemStatus]] = None
    type: Optional[list[WorkItemType]] = None
    project_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_text: Optional[str] = None
    limit: int = 100
    offset: int = 0
```

**Возвращает:** `list[WorkItem]` — отфильтрованный список

---

#### `register_document(work_item_id: int, user: str) -> WorkItem`
Регистрирует получение бумажного документа.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `work_item_id` | `int` | Да | ID рабочего элемента |
| `user` | `str` | Да | Имя пользователя, зарегистрировавшего документ |

**Побочные эффекты:**
- Устанавливает `doc_received_at = datetime.now()`
- Изменяет статус согласно правилам переходов
- Создаёт `WorkLog(STATUS_CHANGE, "Документ зарегистрирован {user}")`

**Правила переходов:**
| Текущий статус | Новый статус | Условие |
|----------------|--------------|---------|
| `NEW` | `REGISTERED` | Всегда |
| `PENDING_CUTS` | `REGISTERED` | Если GNC файлы появились |
| `DOC_NO_FOLDER` | `DOC_NO_FOLDER` | Статус не меняется |

**Возвращает:** `WorkItem` — обновлённая сущность

---

#### `set_status(work_item_id: int, new_status: WorkItemStatus, reason: Optional[str] = None, user: str = "system") -> WorkItem`
Изменяет статус WorkItem.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `work_item_id` | `int` | Да | ID рабочего элемента |
| `new_status` | `WorkItemStatus` | Да | Новый статус |
| `reason` | `Optional[str]` | Нет | Причина изменения |
| `user` | `str` | Нет | Пользователь (по умолчанию "system") |

**Исключения:**
- `ValueError` — если переход недопустим (см. `ALLOWED_TRANSITIONS`)

**Побочные эффекты:**
- Создаёт `WorkLog(STATUS_CHANGE, f"Статус изменён: {old} → {new}. {reason}")`

---

#### `search(query: str) -> list[WorkItem]`
Полнотекстовый поиск по WorkItem.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `query` | `str` | Да | Поисковый запрос |

**Поля для поиска:**
- `folder_name` (partial match)
- `sidra_number` (partial match)
- `project.name` (partial match)

**Возвращает:** `list[WorkItem]` — найденные элементы

---

#### `open_in_explorer(work_item_id: int, node_id: Optional[str] = None) -> None`
Открывает папку WorkItem в проводнике Windows.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `work_item_id` | `int` | Да | ID рабочего элемента |
| `node_id` | `Optional[str]` | Нет | ID узла (для UNC fallback) |

**Логика:**
1. Получить `scan_root` из настроек (`folder_scanner.sidra_scan_path`)
2. Если `scan_root` настроен: `abs_path = scan_root / work_item.folder_path`
3. Иначе: использовать UNC path как fallback
4. Вызвать `subprocess.Popen(["explorer.exe", str(abs_path)])`

---

## Псевдокод

```python
class WorkItemSystem(BaseSystem):
    
    def register_document(self, work_item_id: int, user: str) -> WorkItem:
        wi = self.get(work_item_id)
        wi.doc_received_at = datetime.now()
        
        if wi.status in (WorkItemStatus.NEW, WorkItemStatus.PENDING_CUTS):
            wi.status = WorkItemStatus.REGISTERED
        elif wi.status == WorkItemStatus.DOC_NO_FOLDER:
            pass  # бумага есть, папки нет — статус остаётся
        
        self._log(wi, WorkLogType.STATUS_CHANGE,
                  f"Документ зарегистрирован: {user}")
        self.session.commit()
        return wi
    
    ALLOWED_TRANSITIONS = {
        WorkItemStatus.NEW:          [REGISTERED, IN_PROGRESS, CANCELLED],
        WorkItemStatus.PENDING_CUTS: [REGISTERED, BLOCKED, CANCELLED],
        WorkItemStatus.REGISTERED:   [IN_PROGRESS, CANCELLED],
        WorkItemStatus.IN_PROGRESS:  [ON_HOLD, DONE, BLOCKED, CANCELLED],
        WorkItemStatus.ON_HOLD:      [IN_PROGRESS, CANCELLED],
        WorkItemStatus.BLOCKED:      [IN_PROGRESS, CANCELLED],
        WorkItemStatus.DONE:         [ARCHIVED],
    }
    
    def open_in_explorer(self, work_item_id: int) -> None:
        wi = self.get(work_item_id)
        scan_root = self.sdk.settings.get("folder_scanner.sidra_scan_path")
        if scan_root:
            abs_path = Path(scan_root) / wi.folder_path
        else:
            abs_path = Path(wi.folder_path)  # UNC fallback
        subprocess.Popen(["explorer.exe", str(abs_path)])
```

---

## TDD: Тесты

```python
def test_register_document_transitions_new_to_registered(in_memory_db):
    wi = WorkItem(folder_name="SIDRA-001", status=WorkItemStatus.NEW, ...)
    in_memory_db.add(wi); in_memory_db.commit()
    
    system = WorkItemSystem(session=in_memory_db)
    system.register_document(wi.id, user="foreman1")
    
    wi_updated = in_memory_db.get(WorkItem, wi.id)
    assert wi_updated.status == WorkItemStatus.REGISTERED
    assert wi_updated.doc_received_at is not None

def test_register_document_creates_worklog(in_memory_db):
    wi = WorkItem(status=WorkItemStatus.NEW, ...)
    system = WorkItemSystem(...)
    system.register_document(wi.id, "foreman1")
    
    logs = in_memory_db.exec(select(WorkLog)).all()
    assert any(l.log_type == WorkLogType.STATUS_CHANGE for l in logs)

def test_invalid_status_transition_raises(in_memory_db):
    wi = WorkItem(status=WorkItemStatus.DONE, ...)
    system = WorkItemSystem(...)
    with pytest.raises(ValueError, match="недопустимый переход"):
        system.set_status(wi.id, WorkItemStatus.PENDING_CUTS)

def test_search_by_partial_folder_name(in_memory_db):
    WorkItem.create_many([
        WorkItem(folder_name="SIDRA-353203-SHLAV-2"),
        WorkItem(folder_name="SIDRA-111111-SHLAV-1"),
        WorkItem(folder_name="MIHTAV-2025-07"),
    ])
    system = WorkItemSystem(...)
    results = system.search("353203")
    assert len(results) == 1
    assert results[0].folder_name == "SIDRA-353203-SHLAV-2"
```

---

## Конфигурация

### WorkItemSettings (если требуется)

```python
from pydantic import Field
from docuflow.domain.entities.settings import BaseModuleSettings

class WorkItemSettings(BaseModuleSettings):
    """Настройки модуля WorkItemSystem"""
    
    # scope="global" — синхронизируется через FileBus snapshot
    default_project_name: str = Field(
        default="Default",
        description="Проект по умолчанию, если не указан project_id",
        scope="global"
    )
    
    auto_register_on_scan: bool = Field(
        default=True,
        description="Автоматически регистрировать документ при сканировании GNC",
        scope="global"
    )
    
    # scope="local" — из .env, не синхронизируется
    explorer_timeout_seconds: int = Field(
        default=5,
        description="Таймаут при открытии папки в проводнике",
        scope="local"
    )
```

### Переменные окружения (.env)

```env
# WorkItemSystem настройки (LOCAL, не синхронизируются)
DOCUFLOW_WORK_ITEM__EXPLORER_TIMEOUT_SECONDS=5
```

### Регистрация в SDK

```python
# В features/work_items/system.py
class WorkItemSystem(BaseSystem):
    def __init__(self, config: Config):
        super().__init__(config)
        self.settings = config.settings_registry.get_module_settings("work_item")
```

---

## Definition of Done

```
✓ CRUD работает (create, get, list, update)
✓ register_document: переходы NEW→REGISTERED, PENDING→REGISTERED
✓ register_document: DOC_NO_FOLDER статус остаётся
✓ set_status: недопустимые переходы вызывают ValueError
✓ WorkLog создаётся при каждом изменении статуса
✓ search() по folder_name partial работает
✓ open_in_explorer: resolve из scan_root + UNC fallback
✓ Все тесты проходят с in-memory SQLite
```
