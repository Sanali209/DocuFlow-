# Дизайн-документ: Task Board v2.0 — Единый производственный центр

## 1. Цель

Создать единый Task Board с **2 вкладками**, объединяющий:
- **Производство** — полная иерархия Project→WorkItem→TaskGroup→TaskItem + документы + управление
- **Моя корзина** — задачи оператора + передача смены

Убрать отдельные вкладки Projects и WorkItems, перенести их функционал в единый вид.

## 2. Терминология

| Термин | Определение |
|--------|-------------|
| **Project** | Проект/контракт (например "SHLAV-2"). Контейнер для WorkItems. |
| **WorkItem** | Наряд (папка с файлами), ранее "Sidra". Содержит TaskGroups. |
| **TaskGroup** | Группа задач. НЕ имеет собственного статуса (агрегирует из задач). |
| **TaskItem** | Отдельный GNC-файл (задача резки). Имеет статус, прогресс, узел. |
| **Document** | Любой файл, привязанный к WorkItem (GNC, PDF, чертежи). |

## 3. Архитектура Task Board (2 таба)

```
┌─────────────────────────────────────────────────────────┐
│  [Производство]          [Моя корзина]                  │
└─────────────────────────────────────────────────────────┘
```

### Таб 1: "Производство" — Единый комплексный вид

Объединяет иерархию задач + документы + управление.

#### 3.1 Иерархическая структура

```
▼ ▼ SHLAV-2 [Проект]                              [Редактировать] [Удалить]
│   ▼ ▼ 3455-11-144 [Наряд]                       [Переместить] [Архивировать]
│   │   ▼ ▶ ST37-2 4.0mm [3 задачи] [🔥 В работе] [LASER_1] [Разбить]
│   │   │   ○ 3455-11-144-A.GNC [▶] [⏸] [✓] 3/8 листов
│   │   │   ○ 3455-11-144-B.GNC [▶] [⏸] [✓] 0/5 листов
│   │   ▼ ▶ S235 5.0mm [2 задачи] [⏳ Ожидание] [—] [Назначить]
│   │       ○ 3455-11-145-A.GNC [▶] [Назначить]
│   ▼ 3455-11-145 [Наряд]
│       ▶ ST37-2 6.0mm [1 задача] [✅ Готово] [LASER_2]
│
▼ ▼ VOLTAS-1 [Проект]
│   ▼ 3476-00-042 [Наряд]
│       ▶ SS 1.4003 1.5mm [4 задачи] [⏳ Ожидание]
```

**Уровни раскрытия:**
- **Project** — раскрывается в список WorkItems
- **WorkItem** — раскрывается в список TaskGroups + документы
- **TaskGroup** — раскрывается в список TaskItems
- **TaskItem** — конечный уровень, действия на строке

**Состояние раскрытия сохраняется в БД** (`ViewState`) — при возвращении на вкладку иерархия восстанавливается.

#### 3.2 Двухстрочные строки (Document-style)

Каждая строка иерархии — двухстрочная:
```
Строка 1: Иконка + Название + Бейджи (статус, узел, срочность)
Строка 2: Метаданные + Быстрые действия + Прогресс
```

**WorkItem строка:**
```
📁 3455-11-144                              [3 группы] [8 файлов]
   SHLAV-2 | Создан: 24.01 | Статус: В работе
   [Открыть папку] [Просмотр] [Редактировать] [Переместить в проект ▼]
```

**TaskGroup строка:**
```
📦 ST37-2 4.0mm                             [🔥 В работе] [LASER_1]
   3 задачи | 11/16 листов | 45 мин | DRIFT: +12%
   [▶ Запустить все] [⏸ Пауза все] [Назначить на узел ▼] [Разбить]
```

**TaskItem строка:**
```
📄 3455-11-144-A.GNC                        [▓▓▓░░░░░] 3/8
   ST37-2 4.0mm | LASER_1 | 45 мин (est: 40 мин)
   [▶] [⏸] [+1 лист] [✓ Завершить] [Просмотр GNC]
```

#### 3.3 Раскрытие строки для просмотра/редактирования

Клик на "Просмотр" или двойной клик раскрывает карточку:

```
┌─────────────────────────────────────────────────────────┐
│ 📄 3455-11-144-A.GNC                        [✕ Закрыть]│
├─────────────────────────────────────────────────────────┤
│ Материал: ST37-2 4.0mm                                 │
│ Листов: 8 | Сделано: 3 | Деталей: 47                   │
│ Узел: LASER_1 | Оператор: admin                        │
│                                                         │
│ [Превью SVG]                                           │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ [▶ Начать] [⏸ Пауза] [+1 лист] [✓ Завершить]      ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ История:                                               │
│ 14:32 — Начата admin                                   │
│ 15:10 — Пауза: "Проверка форсунки"                     │
│ 15:25 — Возобновлена admin                             │
│                                                         │
│ [Редактировать] [Архивировать]                         │
└─────────────────────────────────────────────────────────┘
```

#### 3.4 Управление Project

**В шапке таба:**
```
[Создать проект +]  [Комплексные фильтры ▼]  [Пресеты ▼]  [🔍 Поиск]
```

**Действия на Project:**
- Создать (форма: название, описание, дедлайн)
- Редактировать (inline или форма)
- Удалить (с подтверждением, если есть WorkItems)
- Перенести WorkItem в другой Project (drag-and-drop или выбор из списка)

#### 3.5 Управление WorkItem

**Действия на WorkItem:**
- Создать (внутри Project): загрузка папки/файлов
- Редактировать: название, описание, приоритет
- Архивировать (статус ARCHIVED)
- Переместить в другой Project
- Регистрация вручную (без сканера): создание WorkItem + TaskItems вручную

**Регистрация вручную:**
```
[Регистрация наряда +]
  └─ Форма:
     - Название папки
     - Выбор Project
     - Загрузка файлов (GNC, PDF)
     - Материал (выбор из справочника)
     - Количество листов
     - [Создать]
```

#### 3.6 Управление TaskGroup

**Действия на TaskGroup:**
- Авто-группировка по материалу+толщине (helper)
- Ручная группировка (выбрать задачи → "Объединить в группу")
- Разбить группу
- Назначить на узел (создаёт WorkerBucketEntry)
- Убрать с узла (удаляет WorkerBucketEntry)
- Запустить все / Пауза все / Завершить все

#### 3.7 Комплексные фильтры и пресеты

**Панель фильтров** (сворачиваемая):
```
┌─────────────────────────────────────────────────────────┐
│ Фильтры                              [Свернуть ▲]      │
├─────────────────────────────────────────────────────────┤
│ Проект:     [Все ▼] [SHLAV-2 ▼] [VOLTAS-1 ▼]          │
│ Статус Наряда: [☑ NEW] [☑ PENDING_CUTS] [☐ DONE]      │
│ Статус Группы: [☑ PLANNED] [☑ IN_PROGRESS] [☐ DONE]   │
│ Статус Задачи: [☑ PLANNED] [☑ IN_PROGRESS] [☐ DONE]   │
│ Узел:       [Все ▼] [LASER_1 ▼] [LASER_2 ▼]           │
│ Материал:   [Все ▼] [ST37-2 ▼] [S235 ▼]               │
│ Толщина:    [1.0] — [20.0] мм                         │
│ Дата:       [с __________] [по __________]            │
│ Срочные:    [☐ Только срочные]                        │
│                                                         │
│ [Сбросить]  [Применить]  [💾 Сохранить пресет]        │
└─────────────────────────────────────────────────────────┘
```

**Пресеты:**
- Сохраняется в `ViewPreset` (имя, JSON фильтров, пользователь)
- Быстрый выбор из dropdown
- "По умолчанию" — применяется автоматически

### Таб 2: "Моя корзина" — Оператор

```
┌─────────────────────────────────────────────────────────┐
│ LASER_1 | Оператор: admin | 🟢 В работе                │
│ Смена начата: 08:00 | Задач выполнено: 3/12            │
├─────────────────────────────────────────────────────────┤
│ 🔥 В РАБОТЕ СЕЙЧАС                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ST37-2 4.0mm [3 задачи]  DRIFT: +12%               │ │
│ │ [▓▓▓░░░░░] 3/8 листов | 45 мин                      │ │
│ │ ○ 3455-11-144-A.GNC [▶] [⏸] [✓]                    │ │
│ │ ○ 3455-11-144-B.GNC [▶] [⏸] [✓]                    │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ⏳ ОЧЕРЕДЬ НА ПОДГОТОВКУ                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ S235 5.0mm [2 задачи]                               │ │
│ │ [░░░░░░░░░] 0/5 листов | Ожидание                   │ │
│ │ ○ 3455-11-145-A.GNC [▶]                             │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [Сдать смену ▼]                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Передача смены

**Кнопка "Сдать смену"** — клик разворачивает форму прямо в панели:

```
┌─────────────────────────────────────────────────────────┐
│ Сдать смену                                            │
│ Кому: [________________________]                       │
│ Заметка:                                               │
│ [                                                  ]   │
│ [                                                  ]   │
│ [ОТМЕНА]                    [ПОДТВЕРДИТЬ СДАЧУ]      │
└─────────────────────────────────────────────────────────┘
```

**После передачи — входящий баннер** (для следующего оператора):

```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Заметка от предыдущей смены (admin → you)           │
│                                                         │
│ "Проблема с подачей газа на 3-м листе                   │
│  3455-11-144-A, проверьте форсунку"                     │
│                                                         │
│                                     [✓ ПРИНЯТО]       │
└─────────────────────────────────────────────────────────┘
```

- **"Принято"** скрывает баннер, создаёт `WorkLog(HANDOVER_ACCEPTED)`
- Баннер появляется только при выборе узла с `handover_note` для текущего пользователя

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
    view_name TEXT NOT NULL,  -- 'task_board_production'
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
    view_name TEXT NOT NULL,  -- 'task_board_production'
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

## 5. Omnisearch интеграция

Omnisearch ищет по всем уровням иерархии:

| Тип результата | Поля поиска | Действие при клике |
|----------------|-------------|-------------------|
| Project | name, description | Раскрыть проект в табе "Производство" |
| WorkItem | folder_name, sidra_number | Раскрыть наряд в табе "Производство" |
| TaskItem | file_name, file_path | Раскрыть TaskGroup + выделить задачу |
| Document | file_name (любой файл в папке WorkItem) | Перейти в таб "Производство", раскрыть WorkItem |
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

## 6. TaskGroupService (замена BatchEngine)

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

## 7. Миграция данных

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

## 8. API / Backend

### Новые методы TaskBoardSystem

```python
async def get_hierarchy(self, filters=None) -> list[ProjectHierarchy]:
    """Загружает иерархию с применением фильтров."""
    pass

async def move_workitem_to_project(self, work_item_id, project_id):
    """Переместить наряд в другой проект."""
    pass

async def assign_taskgroup_to_node(self, task_group_id, node_id):
    """Назначить группу на узел (создает WorkerBucketEntry)."""
    pass

async def create_workitem_manual(self, project_id, folder_name, files, material):
    """Ручная регистрация наряда (без сканера)."""
    pass
```

### ViewStateSystem

```python
async def save_expansion_state(self, user_id, view_name, states: dict):
    """Сохранить состояние раскрытия."""
    pass

async def load_expansion_state(self, user_id, view_name) -> dict:
    """Загрузить состояние раскрытия."""
    pass
```

### ViewPresetSystem

```python
async def save_preset(self, user_id, name, view_name, filters):
    """Сохранить пресет фильтров."""
    pass

async def get_presets(self, user_id, view_name) -> list[ViewPreset]:
    """Загрузить пресеты пользователя."""
    pass
```

## 9. UI-компоненты

| Компонент | Назначение |
|-----------|-----------|
| `HierarchyTable` | Древовидная таблица с раскрытием уровней |
| `HierarchyRow` | Двухстрочная строка любого уровня |
| `TaskGroupRow` | Строка TaskGroup с агрегированным статусом |
| `TaskItemRow` | Строка задачи с кнопками и прогресс-баром |
| `ExpandableCard` | Раскрывающаяся карточка для просмотра/редактирования |
| `FilterPanel` | Панель комплексных фильтров с пресетами |
| `HandoverForm` | Раскрывающаяся форма передачи смены |
| `HandoverBanner` | Баннер входящей передачи смены |
| `NodeSelector` | Выбор рабочего места (лазера) |

## 10. Критерии приёмки

### Обязательные
- [ ] 2 таба: "Производство" и "Моя корзина"
- [ ] Таб "Производство": иерархия Project→WorkItem→TaskGroup→TaskItem
- [ ] Двухстрочные строки на всех уровнях иерархии
- [ ] Раскрытие/сворачивание уровней с сохранением в DB (ViewState)
- [ ] Переназначение WorkItem между Project'ами
- [ ] Создание/удаление/редактирование Project и WorkItem
- [ ] Регистрация WorkItem вручную (без сканера)
- [ ] Управление TaskGroup: создание, разбиение, назначение на узел
- [ ] Комплексные фильтры с пресетами (ViewPreset)
- [ ] Omnisearch работает по всем уровням иерархии
- [ ] Таб "Моя корзина": TaskGroup'ы на узле + передача смены
- [ ] Передача смены: форма (кнопка → разворот) + входящий баннер + "Принято"
- [ ] TaskGroup — полноценная DB-сущность, batch_group_id удалён

### Опциональные (Phase 2)
- [ ] Drag-and-drop WorkItem между Project'ами
- [ ] Drag-and-drop TaskGroup на узлы
- [ ] Inline editing в раскрытой строке
- [ ] Превью файлов (SVG, PDF) в раскрытой строке
- [ ] Real-time sync между вкладками

## 11. Удаляемый функционал

- Отдельная вкладка "Projects" (функционал в Task Board → Производство)
- Отдельная вкладка "WorkItems" (функционал в Task Board → Производство)
- `batch_engine.py` (заменён на TaskGroupService)
- `batch_group_id` строковый UUID (заменён на `task_group_id` FK)
- Отдельный таб "Передача смены" (теперь внутри "Моя корзина")
- Отдельный таб "Документы" (объединён с "Задачи" в "Производство")

## 12. Файлы для изменения

### Сущности
- `src/docuflow/domain/entities/production.py` — добавить TaskGroup, ViewState, ViewPreset

### Системы
- `src/docuflow/features/task_board/system.py` — иерархия, фильтры, пресеты
- `src/docuflow/features/task_board/task_group_service.py` — замена BatchEngine (НОВЫЙ)
- `src/docuflow/features/task_board/view.py` — единый Task Board (2 таба)

### Виджеты
- `src/docuflow/lib/widgets/hierarchy_table.py` — древовидная таблица (НОВЫЙ)
- `src/docuflow/lib/widgets/hierarchy_row.py` — двухстрочная строка (НОВЫЙ)
- `src/docuflow/lib/widgets/filter_panel.py` — панель фильтров с пресетами (НОВЫЙ)
- `src/docuflow/lib/widgets/handover_form.py` — форма передачи смены (НОВЫЙ)
- `src/docuflow/lib/widgets/handover_banner.py` — баннер входящей смены (НОВЫЙ)

### Другое
- `src/docuflow/features/core/search.py` — обновить Omnisearch
- `src/docuflow/main.py` — убрать регистрацию Projects/WorkItems views (или скрыть)
- `src/docuflow/features/projects/view.py` — отметить deprecated
- `src/docuflow/features/work_items/view.py` — отметить deprecated

## 13. Паллет-трекинг и резервирование материалов

### 13.1 Статус SUSPENDED

Добавить `TaskItemStatus.SUSPENDED` для длительной приостановки задачи.

```python
class TaskItemStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"       # Кратковременная пауза (с указанием причины)
    SUSPENDED = "suspended"   # Длительная приостановка (бригадир/оператор)
    DONE = "done"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
```

**Переходы:**
```python
VALID_TASK_TRANSITIONS = {
    ...
    TaskItemStatus.IN_PROGRESS: [ON_HOLD, SUSPENDED, DONE, BLOCKED, CANCELLED],
    TaskItemStatus.SUSPENDED: [IN_PROGRESS, DONE, CANCELLED],
    ...
}
```

### 13.2 Авто-расчёт произведённых деталей (qty_produced)

При завершении задачи система автоматически считает количество деталей:

```
qty_produced = sum(TaskPart.qty for part in task.parts) * sheets_done
```

- `TaskPart.qty` — количество экземпляров детали в ОДНОМ листе (из GNC)
- `sheets_done` — сколько листов реально порезано
- Оператор НЕ вводит qty_produced вручную

Если `TaskItem.parts` пустой — `qty_produced = sheets_done` (fallback).

### 13.3 Диалог завершения задачи (с паллетой)

```
┌─────────────────────────────────────────────────────────┐
│ Завершить задачу 3455-11-144-A.GNC?                    │
│                                                         │
│ Листов сделано: 8/8                                    │
│ Деталей произведено: 47 (авто)                         │
│                                                         │
│ Куда кладём?                                           │
│ (•) Создать новую паллету                              │
│ ( ) Добавить к существующей: [выбрать ▼]              │
│                                                         │
│ [ОТМЕНА]                    [ЗАВЕРШИТЬ]                │
└─────────────────────────────────────────────────────────┘
```

**При создании новой паллеты:**
```python
pallet = ProductionSystem.register_finished_pallet(
    task_item_id=task.id,
    quantity=auto_calculated_qty_produced,
    author_name=operator_name,
)
# ProductionUnit.label_id = "26-04-LASER_1-0015" (auto)
# ProductionUnit.task_item_id = task.id
```

**При добавлении к существующей:**
```python
existing_pallet = session.get(ProductionUnit, selected_pallet_id)
existing_pallet.qty_produced += auto_calculated_qty_produced
# WorkLog: "Added to pallet X: +47 units from task Y"
```

### 13.4 Связь TaskItem ↔ ProductionUnit

**Прямая связь:** `TaskItem.production_units` (One-to-Many через FK `task_item_id`)

**Обратный поиск (по номеру работы/таска/проекта):**
```python
def find_pallets_by_task(task_id: int) -> list[ProductionUnit]:
    return session.exec(
        select(ProductionUnit).where(ProductionUnit.task_item_id == task_id)
    ).all()

def find_pallets_by_work_item(work_item_id: int) -> list[ProductionUnit]:
    return session.exec(
        select(ProductionUnit)
        .join(TaskItem)
        .where(TaskItem.work_item_id == work_item_id)
    ).all()

def find_pallets_by_project(project_id: int) -> list[ProductionUnit]:
    return session.exec(
        select(ProductionUnit)
        .join(TaskItem)
        .join(WorkItem)
        .where(WorkItem.project_id == project_id)
    ).all()

def find_task_by_pallet_label(label_id: str) -> TaskItem | None:
    pallet = session.exec(
        select(ProductionUnit).where(ProductionUnit.label_id == label_id)
    ).first()
    return pallet.task_item if pallet else None
```

### 13.5 Показ паллет в иерархии

**TaskItemRow (DONE):**
```
📄 3455-11-144-A.GNC                        [✅ Готово]
   ST37-2 4.0mm | LASER_1 | 8/8 листов | 47 деталей
   📦 Паллета: 26-04-LASER_1-0015
   [Просмотр] [Найти на складе]
```

**TaskGroupRow (если есть DONE задачи):**
```
📦 ST37-2 4.0mm [3 задачи] [✅ Готово]
   3/3 задач | 47 деталей | 2 паллеты
   📦 26-04-LASER_1-0015 (47 шт) | 📦 26-04-LASER_1-0016 (12 шт)
```

**WorkItemRow (раскрытый):**
```
📁 3455-11-144
   Паллеты: 26-04-LASER_1-0015, 26-04-LASER_1-0016
   [Показать все паллеты наряда]
```

### 13.6 Резервирование и списание материалов

**Резервирование (бригадир):**
```python
# При назначении TaskGroup на узел
InventorySystem.create_reservation(
    stock_item_id=selected_stock_id,
    work_item_id=work_item_id,
    qty=estimated_sheets,
    is_hard=False,  # soft по умолчанию
)
```

**Списание (авто при DONE):**
```python
# В TaskBoardSystem.complete_task()
InventorySystem.perform_write_off(task_item, sheets_used=sheets_done, author="operator")
# Приоритет: reservation → FIFO fallback
```

**Показ в UI:**
- TaskItemRow: иконка 📦 если материал зарезервирован
- При наведении: "Материал зарезервирован: BATCH-99 (10 листов)"
- При списании: WorkLog запись + аудит MaterialAudit

## 14. Обновлённые критерии приёмки

### Обязательные (добавленные)
- [ ] `TaskItemStatus.SUSPENDED` — длительная приостановка
- [ ] Авто-расчёт `qty_produced` из TaskPart.qty * sheets_done
- [ ] Диалог завершения: "Создать новую паллету" / "Добавить к существующей"
- [ ] Связь TaskItem ↔ ProductionUnit с обратным поиском
- [ ] Показ номера паллеты в TaskItemRow (DONE) и TaskGroupRow
- [ ] Поиск паллет по project/work_item/task_id и обратно
- [ ] Резервирование материала при назначении на узел
- [ ] Авто-списание материала при DONE

### Файлы (добавленные)
- `src/docuflow/domain/entities/production.py` — добавить SUSPENDED в TaskItemStatus
