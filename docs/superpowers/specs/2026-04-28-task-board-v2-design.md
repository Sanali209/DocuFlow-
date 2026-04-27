# Дизайн-документ: Task Board v2.0 — Единый производственный центр

## 1. Цель

Создать единый Task Board, объединяющий:
- **Projects** (CRUD + назначение нарядов)
- **WorkItems** (просмотр, фильтрация, организация)
- **TaskGroups + TaskItems** (производственный трекинг)

Убрать отдельные вкладки Projects и WorkItems, перенести их функционал в Task Board.

## 2. Терминология

| Термин | Определение |
|--------|-------------|
| **Project** | Проект/контракт (например "SHLAV-2"). Контейнер для WorkItems. |
| **WorkItem** | Наряд (папка с файлами), ранее "Sidra". Содержит TaskGroups. |
| **TaskGroup** | Группа задач. НЕ имеет собственного статуса (агрегирует из задач). |
| **TaskItem** | Отдельный GNC-файл (задача резки). Имеет статус, прогресс, узел. |
| **Document** | Любой файл, привязанный к WorkItem (GNC, PDF, чертежи). |

## 3. Архитектура Task Board (3 таба)

```
┌─────────────────────────────────────────────────────────┐
│  [Задачи] [Документы] [Моя корзина] [Передача смены]   │
└─────────────────────────────────────────────────────────┘
```

### Таб 1: "Задачи" — Производственная иерархия

Показывает Project → WorkItem → TaskGroup → TaskItem.

```
▼ ▼ SHLAV-2 [Проект]
│   ▼ ▼ 3455-11-144 [Наряд]
│   │   ▼ ▶ ST37-2 4.0mm [3 задачи] [🔥 В работе] [LASER_1]
│   │   │   ○ 3455-11-144-A.GNC [▶] [⏸] [✓] 3/8 листов
│   │   │   ○ 3455-11-144-B.GNC [▶] [⏸] [✓] 0/5 листов
│   │   ▼ ▶ S235 5.0mm [2 задачи] [⏳ Ожидание] [—]
│   │       ○ 3455-11-145-A.GNC [▶] [⏸] [✓] 0/3 листов
│   ▼ 3455-11-145 [Наряд]
│       ▶ ST37-2 6.0mm [1 задача] [✅ Готово] [LASER_2]
```

**Функции:**
- Раскрытие/сворачивание каждого уровня (состояние в DB: `ViewState`)
- Drag-and-drop WorkItem между Project'ами
- Назначение TaskGroup на узел (кнопка или DnD)
- Создание/разбиение TaskGroup (ручное или авто по материалу)
- Быстрые действия на TaskItem: Старт, Пауза, +1 лист, Завершить
- Прогресс-бар на TaskGroup (средний прогресс задач)

### Таб 2: "Документы" — Файловый менеджер

Двухстрочные строки таблицы, раскрываемые для просмотра/редактирования.

```
┌─────────────────────────────────────────────────────────┐
│ 📁 3455-11-144                    [3 GNC] [2 PDF]       │
│    SHLAV-2 | Создан: 24.01 | Статус: В работе           │
│    [Открыть папку] [Просмотр] [Редактировать]          │
├─────────────────────────────────────────────────────────┤
│ 📄 3455-11-144-A.GNC              ST37-2 4.0mm          │
│    8 листов | LASER_1 | ▓▓▓░░░░░░░ 3/8                 │
│    [▶] [⏸] [+1] [Завершить] [Просмотр GNC]            │
├─────────────────────────────────────────────────────────┤
│ 📄 3455-11-144-B.GNC              S235 5.0mm           │
│    5 листов | Не назначен | ░░░░░░░░░░ 0/5             │
│    [▶] [Назначить] [Просмотр GNC]                      │
└─────────────────────────────────────────────────────────┘
```

**Функции:**
- Двухстрочная строка: название + метаданные + действия
- Раскрытие строки: предпросмотр файла, детали, история
- Редактирование метаданных прямо в строке (inline editing)
- Группировка по WorkItem (как в примере выше) или плоский список
- Фильтры: по типу файла, материалу, статусу, узлу, дате

### Таб 3: "Моя корзина" (только оператор)

TaskGroup'ы, назначенные на текущий узел.

```
┌─────────────────────────────────────────────────────────┐
│ 🔥 В РАБОТЕ СЕЙЧАС                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ST37-2 4.0mm [3 задачи]  DRIFT: +12%                │ │
│ │ [▓▓▓░░░░░] 3/8 листов | 45 мин                       │ │
│ │ ○ 3455-11-144-A.GNC [▶] [⏸] [✓]                     │ │
│ │ ○ 3455-11-144-B.GNC [▶] [⏸] [✓]                     │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ⏳ ОЧЕРЕДЬ НА ПОДГОТОВКУ                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ S235 5.0mm [2 задачи]                                │ │
│ │ [░░░░░░░░░] 0/5 листов | Ожидание                    │ │
│ │ ○ 3455-11-145-A.GNC [▶]                             │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Таб 4: "Передача смены"

**Форма отправки:**
```
┌─────────────────────────────────────────┐
│ Передать смену на LASER_1              │
│                                         │
│ Кому: [________________]               │
│ Заметка:                               │
│ [                                    ] │
│ [                                    ] │
│                                         │
│ [ОТМЕНА]    [ПЕРЕДАТЬ СМЕНУ]         │
└─────────────────────────────────────────┘
```

**Входящее сообщение (баннер):**
```
┌─────────────────────────────────────────┐
│ ⚠️ Заметка от предыдущей смены          │
│                                         │
│ "Проблема с подачей газа на 3-м листе   │
│ 3455-11-144-A, проверьте форсунку"      │
│                                         │
│                [ПРИНЯТО]               │
└─────────────────────────────────────────┘
```

## 4. DB Schema Changes

### Новые таблицы

```sql
-- TaskGroup (замена batch_group_id)
CREATE TABLE taskgroup (
    id INTEGER PRIMARY KEY,
    name TEXT,
    work_item_id INTEGER NOT NULL REFERENCES workitem(id),
    created_by TEXT,
    grouping_rule TEXT DEFAULT 'manual',  -- 'manual' | 'auto_material'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ViewState (состояние раскрытия уровней)
CREATE TABLE viewstate (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    view_name TEXT NOT NULL,  -- 'task_board_tasks' | 'task_board_docs'
    entity_type TEXT NOT NULL,  -- 'project' | 'workitem' | 'taskgroup'
    entity_id TEXT NOT NULL,
    is_expanded BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, view_name, entity_type, entity_id)
);

-- ViewPreset (сохраненные фильтры)
CREATE TABLE viewpreset (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    view_name TEXT NOT NULL,  -- 'task_board_tasks' | 'task_board_docs'
    filters_json TEXT NOT NULL,  -- JSON с фильтрами
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Изменения существующих таблиц

```sql
-- TaskItem: batch_group_id -> task_group_id
ALTER TABLE taskitem ADD COLUMN task_group_id INTEGER REFERENCES taskgroup(id);
-- Миграция: создать TaskGroup для каждого уникального batch_group_id
-- UPDATE taskitem SET task_group_id = ...;
-- ALTER TABLE taskitem DROP COLUMN batch_group_id;

-- WorkerBucketEntry: batch_group_id -> task_group_id
ALTER TABLE workerbucketentry ADD COLUMN task_group_id INTEGER;
-- UPDATE workerbucketentry SET task_group_id = ...;
-- ALTER TABLE workerbucketentry DROP COLUMN batch_group_id;
```

## 5. Иерархические фильтры и пресеты

### Фильтры (таб "Задачи")

| Фильтр | Тип | Описание |
|--------|-----|----------|
| Project | multi-select | Показывать только выбранные проекты |
| WorkItem status | multi-select | NEW, PENDING_CUTS, IN_PROGRESS, DONE... |
| TaskGroup status | multi-select | PLANNED, IN_PROGRESS, DONE, MIXED |
| TaskItem status | multi-select | PLANNED, IN_PROGRESS, ON_HOLD, DONE... |
| Node | multi-select | LASER_1, LASER_2... |
| Material | multi-select | ST37-2, S235... |
| Thickness | range | 1.0 - 20.0 мм |
| Date range | date | Создан, Начат, Завершен |
| Urgent only | checkbox | Только срочные |

### Фильтры (таб "Документы")

| Фильтр | Тип | Описание |
|--------|-----|----------|
| File type | multi-select | GNC, PDF, DWG... |
| WorkItem | multi-select | Конкретные наряды |
| Material | multi-select | По материалу файла |
| Node | multi-select | Назначенный узел |
| Status | multi-select | Статус связанного TaskItem |
| Has preview | checkbox | Только с превью |

### Пресеты

- Пользователь сохраняет набор фильтров как именованный пресет
- Пресет хранится в `ViewPreset` (JSON фильтров)
- Можно установить пресет по умолчанию
- Быстрый выбор пресета из dropdown

## 6. Компоненты UI

### Древовидная таблица (таб "Задачи")

```python
class HierarchyTable:
    def __init__(self, user_id, view_name, system_scope):
        self.user_id = user_id
        self.view_name = view_name  # 'task_board_tasks'
        self.system_scope = system_scope
    
    def render_project_row(self, project, level=0):
        # ▼/▶ + название проекта + счетчики
        # Кнопки: [Создать наряд] [Редактировать] [Удалить]
        pass
    
    def render_workitem_row(self, workitem, level=1):
        # ▼/▶ + название наряда + статус + кол-во TaskGroups
        # Drag handle для перемещения между проектами
        pass
    
    def render_taskgroup_row(self, taskgroup, level=2):
        # ▼/▶ + название группы + [статус] + [узел] + [прогресс]
        # Кнопки: [Назначить на узел] [Разбить] [Объединить]
        pass
    
    def render_taskitem_row(self, taskitem, level=3):
        # Название файла + прогресс-бар + кнопки действий
        pass
```

### Двухстрочная таблица (таб "Документы")

```python
class DocumentRow:
    def __init__(self, workitem_or_taskitem, is_group_header=False):
        self.entity = workitem_or_taskitem
        self.is_group_header = is_group_header
        self.is_expanded = False
    
    def render_collapsed(self):
        # Строка 1: иконка + название + бейджи
        # Строка 2: метаданные + кнопки действий
        pass
    
    def render_expanded(self):
        # render_collapsed() + превью + детали + inline editing
        pass
```

### Комплексные фильтры

```python
class FilterPanel:
    def __init__(self, view_name, on_apply):
        self.view_name = view_name
        self.filters = {}  # текущие значения
        self.presets = []  # загруженные пресеты
    
    def render(self):
        # Секции фильтров (свернутые/развернутые)
        # Кнопки: [Применить] [Сбросить] [Сохранить пресет]
        # Dropdown: [Выбрать пресет ▼]
        pass
    
    def save_preset(self, name):
        # Сохранить в ViewPreset
        pass
    
    def load_preset(self, preset_id):
        # Загрузить фильтры из ViewPreset
        pass
```

## 7. ViewState (состояние раскрытия)

```python
class ViewStateService:
    def get_expanded(self, user_id, view_name, entity_type, entity_id) -> bool:
        # Загрузить из viewstate или default=True
        pass
    
    def set_expanded(self, user_id, view_name, entity_type, entity_id, is_expanded):
        # Upsert в viewstate
        pass
    
    def get_all_expanded(self, user_id, view_name):
        # Вернуть dict {(entity_type, entity_id): is_expanded}
        pass
```

## 8. Omnisearch интеграция

Omnisearch должен искать по всем уровням иерархии:

| Тип результата | Поля поиска | Действие при клике |
|----------------|-------------|-------------------|
| Project | name, description | Раскрыть проект в табе "Задачи" |
| WorkItem | folder_name, sidra_number | Раскрыть наряд в табе "Задачи" |
| TaskItem | file_name, file_path | Раскрыть TaskGroup + выделить задачу |
| Document | file_name (любой файл в папке WorkItem) | Перейти в таб "Документы", раскрыть |
| Part | sku, name | Открыть Parts view с фильтром |

```python
class Omnisearch:
    def search(self, query):
        # Поиск по Project, WorkItem, TaskItem, Document
        # Возвращает типизированные результаты
        pass
    
    def navigate_to_result(self, result):
        # Переключить таб, раскрыть уровни, выделить элемент
        # Использовать ViewState для раскрытия родителей
        pass
```

## 9. TaskGroupService (замена BatchEngine)

```python
class TaskGroupService:
    def auto_group_by_material(self, work_item_id) -> list[TaskGroup]:
        """Группировка TaskItem по материалу+толщине."""
        pass
    
    def create_manual_group(self, task_ids, name=None) -> TaskGroup:
        """Ручная группировка задач."""
        pass
    
    def move_task_to_group(self, task_id, group_id) -> None:
        """Переместить задачу в другую группу."""
        pass
    
    def split_group(self, group_id, task_ids) -> TaskGroup:
        """Разделить группу на две."""
        pass
    
    def merge_groups(self, group_ids) -> TaskGroup:
        """Объединить несколько групп."""
        pass
    
    def get_group_status(self, group: TaskGroup) -> TaskGroupStatus:
        """Агрегация статуса из задач."""
        # IN_PROGRESS если хоть одна IN_PROGRESS
        # DONE если все DONE
        # PLANNED если все PLANNED
        # MIXED иначе
        pass
    
    def get_group_progress(self, group: TaskGroup) -> float:
        """Средний прогресс задач в группе."""
        pass
```

## 10. Миграция данных

### Phase 1: Создать TaskGroup таблицу
```python
# Для каждого уникального TaskItem.batch_group_id:
#   1. Найти work_item_id (через TaskItem)
#   2. Создать TaskGroup(name=auto, work_item_id=..., grouping_rule='auto_material')
#   3. Обновить TaskItem.task_group_id = новый_id
```

### Phase 2: Обновить WorkerBucketEntry
```python
# batch_group_id -> task_group_id (lookup через TaskGroup)
```

### Phase 3: Удалить старые колонки
```python
# ALTER TABLE taskitem DROP COLUMN batch_group_id
# ALTER TABLE workerbucketentry DROP COLUMN batch_group_id
```

### Phase 4: Удалить batch_engine.py
```python
# Перенести полезные методы в TaskGroupService
# Удалить BatchEngine, BatchRule, BatchGroup dataclasses
```

## 11. API / Backend

### Новые endpoints (или системные методы)

```python
# TaskBoardSystem
async def get_hierarchy(self, filters=None) -> list[ProjectHierarchy]:
    """Загружает иерархию с применением фильтров."""
    pass

async def move_workitem_to_project(self, work_item_id, project_id):
    """Переместить наряд в другой проект."""
    pass

async def assign_taskgroup_to_node(self, task_group_id, node_id):
    """Назначить группу на узел (создает WorkerBucketEntry)."""
    pass

# ViewStateSystem
async def save_expansion_state(self, user_id, view_name, states: dict):
    """Сохранить состояние раскрытия."""
    pass

async def load_expansion_state(self, user_id, view_name) -> dict:
    """Загрузить состояние раскрытия."""
    pass

# ViewPresetSystem
async def save_preset(self, user_id, name, view_name, filters):
    """Сохранить пресет фильтров."""
    pass

async def get_presets(self, user_id, view_name) -> list[ViewPreset]:
    """Загрузить пресеты пользователя."""
    pass
```

## 12. Критерии приёмки

### Обязательные
- [ ] Таб "Задачи": иерархия Project→WorkItem→TaskGroup→TaskItem
- [ ] Таб "Документы": двухстрочные строки, раскрытие для просмотра/редактирования
- [ ] Таб "Моя корзина": TaskGroup'ы на узле с кнопками управления
- [ ] Таб "Передача смены": форма + входящий баннер + кнопка "Принято"
- [ ] Раскрытие/сворачивание уровней с сохранением в DB (ViewState)
- [ ] Комплексные фильтры с пресетами (ViewPreset)
- [ ] Omnisearch работает по всем уровням иерархии
- [ ] TaskGroup — полноценная DB-сущность, batch_group_id удалён

### Опциональные (Phase 2)
- [ ] Drag-and-drop WorkItem между Project'ами
- [ ] Drag-and-drop TaskGroup на узлы
- [ ] Inline editing в DocumentRow
- [ ] Превью файлов в раскрытой DocumentRow
- [ ] Real-time sync фильтров между вкладками

## 13. Удаляемый функционал

- Отдельная вкладка "Projects" (функционал перенесён в Task Board)
- Отдельная вкладка "WorkItems" (функционал перенесён в Task Board)
- `batch_engine.py` (заменён на TaskGroupService)
- `batch_group_id` строковый UUID (заменён на `task_group_id` FK)

## 14. Файлы для изменения

### Сущности
- `src/docuflow/domain/entities/production.py` — добавить TaskGroup, ViewState, ViewPreset

### Системы
- `src/docuflow/features/task_board/system.py` — иерархия, фильтры, пресеты
- `src/docuflow/features/task_board/task_group_service.py` — замена BatchEngine (НОВЫЙ)
- `src/docuflow/features/task_board/view.py` — единый Task Board (3-4 таба)

### Виджеты
- `src/docuflow/lib/widgets/hierarchy_table.py` — древовидная таблица (НОВЫЙ)
- `src/docuflow/lib/widgets/document_row.py` — двухстрочная строка (НОВЫЙ)
- `src/docuflow/lib/widgets/filter_panel.py` — панель фильтров с пресетами (НОВЫЙ)
- `src/docuflow/lib/widgets/handover_banner.py` — баннер входящей смены (НОВЫЙ)

### Другое
- `src/docuflow/features/core/search.py` — обновить Omnisearch
- `src/docuflow/main.py` — убрать регистрацию Projects/WorkItems views (или скрыть)
- `src/docuflow/features/projects/view.py` — отметить deprecated
- `src/docuflow/features/work_items/view.py` — отметить deprecated
