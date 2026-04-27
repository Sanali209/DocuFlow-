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

## 15. Интеграция Part Library, Warehouse и Finished Pallets

### 15.1 Part Library (Каталог деталей)

**Сейчас:** Отдельная вкладка "Parts" с таблицей деталей, превью SVG, фильтрами.

**Интеграция с Task Board:**

**A. Из TaskItem → Part Library**
```
📄 3455-11-144-A.GNC
   Детали: BASE (×4), P1 (×2), T1 (×1)
   [🔍 BASE] [🔍 P1] [🔍 T1]  ← клик открывает Part Library с фильтром по SKU
```

Клик на SKU детали в TaskItemRow открывает **модальное окно** с Part Preview:
```
┌─────────────────────────────────────────────────────────┐
│ Деталь: BASE-3476-00-042-A                              │
│                                                         │
│ [SVG PREVIEW]                                          │
│                                                         │
│ Материал: ST37-2 4.0mm                                 │
│ Размеры: 120×80 мм | Контуров: 5 | Отверстий: 2       │
│                                                         │
│ Используется в:                                        │
│   • 3455-11-144-A.GNC (8 листов, LASER_1)             │
│   • 3476-00-042-B.GNC (5 листов, LASER_2)             │
│                                                         │
│ [Открыть в Part Library]  [Закрыть]                    │
└─────────────────────────────────────────────────────────┘
```

**B. Из Part Library → Task Board**
- PartLibraryView добавить колонку "Используется в задачах"
- Клик показывает список TaskItems с этой деталью
- Кнопка "Показать в производстве" — переключает на Task Board с фильтром по SKU

### 15.2 Warehouse (Склад материалов)

**Сейчас:** Отдельная вкладка "Warehouse" с каталогом, остатками, очередью подачи, историей.

**Интеграция с Task Board:**

**A. Показ резервирований в иерархии**
```
📦 ST37-2 4.0mm [3 задачи] [🔥 В работе] [LASER_1]
   📦 Материал зарезервирован: BATCH-99 (10 листов)
   [Снять резерв] [Заменить партию]
```

**B. Резервирование прямо из Task Board**
- Бригадир нажимает "Зарезервировать материал" на TaskGroup
- Открывается модальное окно со списком доступных партий:
```
┌─────────────────────────────────────────────────────────┐
│ Резервировать материал для ST37-2 4.0mm                │
│                                                         │
│ Доступные партии:                                      │
│   (•) BATCH-99 — 15 листов (MAIN)                     │
│   ( ) BATCH-101 — 8 листов (A-02)                     │
│   ( ) BATCH-105 — 20 листов (MAIN)                    │
│                                                         │
│ Количество: [10____] листов                            │
│ Тип резерва: [Soft ▼]                                  │
│                                                         │
│ [ОТМЕНА]                    [ЗАРЕЗЕРВИРОВАТЬ]          │
└─────────────────────────────────────────────────────────┘
```

**C. Warehouse view — новая вкладка "РЕЗЕРВЫ"**
```
┌─────────────────────────────────────────────────────────┐
│ [КАТАЛОГ] [ОСТАТКИ] [РЕЗЕРВЫ] [ОЧЕРЕДЬ] [ИСТОРИЯ]    │
├─────────────────────────────────────────────────────────┤
│ Резервы по производству:                               │
│ ┌─────────────────────────────────────────────────────┐│
│ │ BATCH-99 → 3455-11-144 (SHLAV-2) | 10 листов       ││
│ │         [Снять] [Перевести в hard]                 ││
│ └─────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────┐│
│ │ BATCH-101 → 3476-00-042 (VOLTAS-1) | 5 листов      ││
│ │         [Снять] [Перевести в hard]                 ││
│ └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 15.3 Finished Pallets (ProductionUnit)

**Сейчас:** Отдельная вкладка "Production" с таблицей паллет, поиском, ship/split/merge.

**Интеграция с Task Board:**

**A. Паллеты в иерархии (уже описано в 13.5)**
- TaskItemRow (DONE): показывает `📦 Паллета: 26-04-LASER_1-0015`
- TaskGroupRow: список паллет группы
- WorkItemRow: кнопка "Показать все паллеты наряда"

**B. Обратный поиск по номеру паллеты**
- Omnisearch ищет по `ProductionUnit.label_id`
- Результат клика: раскрыть Task Board до TaskItem + выделить

**C. Управление паллетами из Task Board**
- Клик на паллету в TaskItemRow → модальное окно:
```
┌─────────────────────────────────────────────────────────┐
│ Паллета: 26-04-LASER_1-0015                            │
│                                                         │
│ Деталей: 47 шт                                         │
│ Создана: 26.04 14:32 | Оператор: admin                │
│ Задача: 3455-11-144-A.GNC                              │
│                                                         │
│ [Разделить] [Объединить] [Отгрузить] [Найти на складе] │
└─────────────────────────────────────────────────────────┘
```

**D. Production view — остаётся как обзорный склад**
- Все паллеты системы (не только связанные с задачами)
- Поиск, фильтры, ship/split/merge
- Новая колонка "Связанная задача" с deeplink в Task Board

### 15.4 Omnisearch — обновление

| Тип результата | Поля поиска | Действие |
|----------------|-------------|----------|
| Project | name, description | Раскрыть в "Производство" |
| WorkItem | folder_name, sidra_number | Раскрыть в "Производство" |
| TaskItem | file_name, file_path | Раскрыть + выделить |
| Document | file_name | Раскрыть WorkItem |
| **ProductionUnit** | **label_id** | **Показать TaskItem + паллету** |
| **Part (SKU)** | **sku, name** | **Открыть Part Library** |
| MaterialType | code | Открыть Warehouse с фильтром |

## 16. Интеграция Chat, Incidents, Analytics, Reports

### 16.1 Chat

**Сейчас:** 3 канала (General, Supply & Orders, Failure Log). Сообщения типов MESSAGE, ORDER, INCIDENT.

**Обновления:**

**A. Новый тип сообщения: HANDOVER**
```python
class ChatMessageType(StrEnum):
    MESSAGE = "message"
    ORDER = "order"
    INCIDENT = "incident"
    HANDOVER = "handover"  # ← новый
```

При передаче смены создаётся `ChatMessage(HANDOVER)` с текстом заметки.

**B. Deeplink на TaskItem в сообщениях**
```
[14:32] admin: Проблема с задачей #1234
              ↓ клик
       → Раскрыть Task Board до TaskItem 1234
```

Парсинг `#<id>` в тексте сообщения → кликабельная ссылка.

**C. Новый канал: "Производство"**
```
[General Feed] [Supply & Orders] [Failure Log] [Производство]
```

Канал "Производство" показывает:
- HANDOVER сообщения
- Завершённые задачи (auto: "✅ TaskItem 1234 завершена, паллета 26-04-0015")
- Резервирования материалов

### 16.2 Incidents

**Сейчас:** Таблица активных блокеров + история. Фильтр по группе (Foreman, Maintenance, Supply, IT).

**Обновления:**

**A. Deeplink на TaskItem**
```
┌─────────────────────────────────────────────────────────┐
│ BREAKDOWN | → Maintenance | FAIL-ID: 42                │
│ Описание: Поломка лазера                                 │
│ Задача: #1234  ← клик → раскрыть Task Board            │
│ [Claim] [Resolve]                                       │
└─────────────────────────────────────────────────────────┘
```

**B. Фильтр по Project/WorkItem**
```
[Все проекты ▼] [Все наряды ▼] [ALL] [Foreman] [Maintenance]...
```

**C. Интеграция с Task Board**
- Кнопка "Создать инцидент" в TaskItemRow (в дополнение к BLOCKED)
- Инцидент автоматически привязывается к `task_item_id`

### 16.3 Analytics

**Сейчас:** KPI: Total Work Items, Avg Drift, Total Finished Parts, Status Distribution pie chart, 7-day output bar chart.

**Новые метрики:**

```python
metrics = {
    # Существующие
    "total_work_items": ...,
    "total_tasks": ...,
    "total_pallets": ...,
    "total_parts_produced": ...,
    "avg_drift": ...,
    "completion_rate": ...,
    "status_counts": ...,
    
    # Новые
    "total_task_groups": ...,           # Всего TaskGroup
    "avg_group_size": ...,              # Среднее задач в группе
    "groups_by_status": {               # TaskGroup по статусам
        "planned": ..., "in_progress": ..., "done": ..., "mixed": ...
    },
    "node_utilization": {               # Загрузка узлов
        "LASER_1": {"active": 2, "queued": 3, "done": 10},
        "LASER_2": {"active": 1, "queued": 1, "done": 5},
    },
    "material_reservation_rate": ...,   # % нарядов с резервом
    "pallet_by_project": {              # Паллеты по проектам
        "SHLAV-2": 15, "VOLTAS-1": 8
    },
}
```

**Новые графики:**

**График 3: Загрузка узлов (stacked bar)**
```
LASER_1  [▓▓▓░░░░░] 3/8 активных
LASER_2  [▓░░░░░░░░] 1/5 активных
```

**График 4: TaskGroup статусы (donut)**
```
[PLANNED 30%] [IN_PROGRESS 20%] [DONE 40%] [MIXED 10%]
```

### 16.4 Reports

**Сейчас:** Шаблоны отчётов (shift_summary), фильтры по дате, HTML preview, PDF export.

**Новые ReportDataBlocks:**

```python
# task_group_summary
{
    "name": "task_group_summary",
    "label": "Task Group Summary",
    "query_fn": lambda session, params: [...]  # Список TaskGroup с задачами
}

# material_reservation_status
{
    "name": "material_reservation_status",
    "label": "Material Reservations",
    "query_fn": lambda session, params: [...]  # Резервы с привязкой к нарядам
}

# pallet_by_project
{
    "name": "pallet_by_project",
    "label": "Pallets by Project",
    "query_fn": lambda session, params: [...]  # Паллеты сгруппированные по проектам
}

# node_performance
{
    "name": "node_performance",
    "label": "Node Performance",
    "query_fn": lambda session, params: [...]  # Drift, uptime по узлам
}
```

**Новые шаблоны:**
- `"production_summary"` — иерархия Project→WorkItem→TaskGroup→TaskItem
- `"material_audit"` — резервы, списания, остатки
- `"pallet_manifest"` — список паллет с номерами и привязкой к задачам

## 17. Обновлённые критерии приёмки

### Обязательные (добавленные)
- [ ] `TaskItemStatus.SUSPENDED` — длительная приостановка
- [ ] Авто-расчёт `qty_produced` из TaskPart.qty * sheets_done
- [ ] Диалог завершения: "Создать новую паллету" / "Добавить к существующей"
- [ ] Связь TaskItem ↔ ProductionUnit с обратным поиском
- [ ] Показ номера паллеты в TaskItemRow (DONE) и TaskGroupRow
- [ ] Поиск паллет по project/work_item/task_id и обратно
- [ ] Резервирование материала при назначении на узел
- [ ] Авто-списание материала при DONE
- [ ] **Part Library: клик на деталь в TaskItem → модальное окно с превью + список задач**
- [ ] **Part Library: кнопка "Показать в производстве" с фильтром по SKU**
- [ ] **Warehouse: резервирование материала прямо из Task Board (модальное окно)**
- [ ] **Warehouse: новая вкладка "РЕЗЕРВЫ" с привязкой к нарядам**
- [ ] **Production: обратный поиск по label_id в Omnisearch**
- [ ] **Production: deeplink из паллеты в Task Board**
- [ ] **Chat: тип HANDOVER, deeplink #<task_id>, канал "Производство"**
- [ ] **Incidents: deeplink на TaskItem, фильтр по Project/WorkItem**
- [ ] **Analytics: метрики TaskGroup, node_utilization, pallet_by_project**
- [ ] **Reports: data blocks task_group_summary, material_reservation, pallet_by_project**

## 18. Модальные окна просмотра/редактирования (таб "Документы")

Каждая сущность в иерархии имеет кнопку "Просмотр/Редактирование" — клик открывает модальное окно с полной информацией.

### 18.1 Project Modal

```
┌─────────────────────────────────────────────────────────┐
│ 📁 Проект: SHLAV-2                          [✕]        │
├─────────────────────────────────────────────────────────┤
│ Название: [SHLAV-2________________________]           │
│ Описание: [Контракт на резку деталей...    ]           │
│ Дедлайн: [2025-12-31____]                              │
│ Статус: [Активный ▼]                                   │
│                                                         │
│ Нарядов: 12 | Активных: 5 | Завершено: 7              │
│                                                         │
│ ┌─ Наряды проекта ─────────────────────────────────┐   │
│ │ 3455-11-144 [В работе]                           │   │
│ │ 3476-00-042 [Готово]                             │   │
│ │ ...                                              │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ [Сохранить] [Удалить] [Закрыть]                        │
└─────────────────────────────────────────────────────────┘
```

### 18.2 WorkItem Modal

```
┌─────────────────────────────────────────────────────────┐
│ 📂 Наряд: 3455-11-144                       [✕]        │
├─────────────────────────────────────────────────────────┤
│ Папка: [3455-11-144________________________]           │
│ Проект: [SHLAV-2 ▼]                                    │
│ SIDRA: [3455-11-144________]                           │
│ Статус: [В работе ▼]                                   │
│                                                         │
│ ┌─ Файлы ──────────────────────────────────────────┐   │
│ │ 📄 3455-11-144-A.GNC  ST37-2 4.0mm  [Просмотр]  │   │
│ │ 📄 3455-11-144-B.GNC  S235 5.0mm   [Просмотр]  │   │
│ │ 📄 чертеж.pdf                                   │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─ Группы задач ───────────────────────────────────┐   │
│ │ ST37-2 4.0mm [3 задачи] [🔥 В работе]            │   │
│ │ S235 5.0mm [2 задачи] [⏳ Ожидание]              │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ [Сохранить] [Архивировать] [Удалить] [Закрыть]        │
└─────────────────────────────────────────────────────────┘
```

### 18.3 TaskGroup Modal

```
┌─────────────────────────────────────────────────────────┐
│ 📦 Группа: ST37-2 4.0mm (3 задачи)          [✕]        │
├─────────────────────────────────────────────────────────┤
│ Название: [ST37-2 4.0mm____________________]           │
│ Наряд: 3455-11-144                                     │
│ Создана: auto_material | Бригадир: admin              │
│                                                         │
│ Статус: 🔥 В работе                                    │
│ Прогресс: [▓▓▓░░░░░] 3/8 листов                       │
│ Узел: LASER_1                                          │
│                                                         │
│ ┌─ Задачи ─────────────────────────────────────────┐   │
│ │ □ 3455-11-144-A.GNC [▓▓▓░░░░░] 3/8 [▶] [⏸] [✓]│   │
│ │ □ 3455-11-144-B.GNC [░░░░░░░░░] 0/8 [▶] [⏸] [✓]│   │
│ │ □ 3455-11-144-C.GNC [░░░░░░░░░] 0/8 [▶] [⏸] [✓]│   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ [Назначить на узел] [Разбить группу] [Закрыть]        │
└─────────────────────────────────────────────────────────┘
```

### 18.4 TaskItem Modal (с превью неста)

```
┌─────────────────────────────────────────────────────────┐
│ 📄 Задача: 3455-11-144-A.GNC                [✕]        │
├─────────────────────────────────────────────────────────┤
│ Название: [3455-11-144-A.GNC_______________]           │
│ Материал: ST37-2 4.0mm                                 │
│ Толщина: 4.0 мм | Листов: 8                            │
│ Сделано: [3___] / 8                                    │
│ Статус: [В работе ▼]                                   │
│ Узел: [LASER_1 ▼]                                      │
│ Оператор: admin                                        │
│                                                         │
│ ┌─ ПРЕВЬЮ НЕСТА ───────────────────────────────────┐   │
│ │                                                    │   │
│ │    [SVG — полная раскладка деталей на листе]     │   │
│ │                                                    │   │
│ │    Лист: 3000×1500 мм                             │   │
│ │    Детали: BASE(×4), P1(×2), T1(×1)               │   │
│ │                                                    │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─ Детали ─────────────────────────────────────────┐   │
│ │ BASE-3476-00-042-A (×4) [🔍 Просмотр]            │   │
│ │ P1-3476-00-043-A (×2) [🔍 Просмотр]              │   │
│ │ T1-3476-00-044-A (×1) [🔍 Просмотр]              │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─ История ────────────────────────────────────────┐   │
│ │ 14:32 — Начата admin                              │   │
│ │ 15:10 — Пауза: "Проверка форсунки"               │   │
│ │ 15:25 — Возобновлена admin                       │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ [▶ Старт] [⏸ Пауза] [+1 лист] [✓ Завершить]          │
│ [Сохранить] [Создать инцидент] [Закрыть]              │
└─────────────────────────────────────────────────────────┘
```

### 18.5 Pallet (ProductionUnit) Modal

```
┌─────────────────────────────────────────────────────────┐
│ 📦 Паллета: 26-04-LASER_1-0015              [✕]        │
├─────────────────────────────────────────────────────────┤
│ Номер: 26-04-LASER_1-0015                              │
│ Задача: 3455-11-144-A.GNC                              │
│ Наряд: 3455-11-144 | Проект: SHLAV-2                   │
│                                                         │
│ Деталей: 47 шт                                         │
│ Создана: 26.04 14:32 | Оператор: admin                │
│ Место хранения: [A-02-3 ▼]                             │
│                                                         │
│ ┌─ Детали в паллете ───────────────────────────────┐   │
│ │ BASE-3476-00-042-A (×20)                          │   │
│ │ P1-3476-00-043-A (×15)                            │   │
│ │ T1-3476-00-044-A (×12)                            │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ [Разделить] [Объединить] [Отгрузить]                   │
│ [Найти задачу] [Закрыть]                               │
└─────────────────────────────────────────────────────────┘
```

## 19. Превью неста (Nesting Preview)

**Технология:** SVG-рендеринг раскладки деталей на листе.

**Данные из GNC:**
- Размер листа (sheet_x, sheet_y)
- Позиции и количество каждой детали (TaskPart с координатами)
- SVG-контуры деталей из PartLibrary.svg_preview_path

**Рендеринг:**
```python
def render_nest_preview(task_item: TaskItem) -> str:
    """Генерирует SVG с раскладкой деталей на листе."""
    sheet_w = task_item.sheet_x or 3000
    sheet_h = task_item.sheet_y or 1500
    
    # SVG viewBox = размер листа
    svg = f'<svg viewBox="0 0 {sheet_w} {sheet_h}">'
    svg += f'<rect width="{sheet_w}" height="{sheet_h}" fill="#f0f0f0" stroke="#333"/>'
    
    # Для каждой детали в TaskItem.parts:
    #   - Загрузить SVG контур из PartLibrary
    #   - Разместить на позиции (x, y) из GNC
    #   - Добавить label с SKU
    
    for part in task_item.parts:
        # part.position_x, part.position_y — из парсера GNC
        # part.part_sku — для поиска в PartLibrary
        svg += f'<g transform="translate({part.x}, {part.y})">...контур...</g>'
    
    svg += '</svg>'
    return svg
```

**В UI:**
- TaskItem Modal: большой блок с SVG (масштабируемый)
- TaskItemRow (в иерархии): миниатюра неста (thumbnail)

## 20. Part Library — корзина заказа деталей и генерация Rework nests

### 20.1 Скрывающаяся панель корзины

```
┌─────────────────────────────────────────────────────────┐
│ [Part Library]                              [🛒 Корзина ▼] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─ Корзина ────────────────────────────────────────┐   │
│ │ Детали для заказа:                                 │   │
│ │ BASE-3476-00-042-A [×4___] [✕]                    │   │
│ │ P1-3476-00-043-A   [×2___] [✕]                    │   │
│ │ T1-3476-00-044-A   [×1___] [✕]                    │   │
│ │                                                    │   │
│ │ [Очистить]  [Создать заказ ▼]                     │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─ Детали ─────────────────────────────────────────┐   │
│ │ [🔍 Поиск] [Материал ▼] [Размер ▼]               │   │
│ │                                                    │   │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │   │
│ │ │ [SVG]       │ │ [SVG]       │ │ [SVG]       │  │   │
│ │ │ BASE-042-A  │ │ P1-043-A    │ │ T1-044-A    │  │   │
│ │ │ 120×80 мм   │ │ 80×60 мм    │ │ 45×30 мм    │  │   │
│ │ │ [🛒 +]      │ │ [🛒 +]      │ │ [🛒 +]      │  │   │
│ │ └─────────────┘ └─────────────┘ └─────────────┘  │   │
│ └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 20.2 Создание заказа (Rework)

**Клик "Создать заказ" → форма:**
```
┌─────────────────────────────────────────────────────────┐
│ Создать новый заказ (Rework)                           │
│                                                         │
│ Название Sidra: [REWORK-001________________________]   │
│ Проект: [Rework ▼] (или выбрать существующий)         │
│                                                         │
│ Детали в заказе:                                       │
│   BASE-3476-00-042-A — 4 шт                            │
│   P1-3476-00-043-A   — 2 шт                            │
│   T1-3476-00-044-A   — 1 шт                            │
│                                                         │
│ [ОТМЕНА]                    [СОЗДАТЬ ЗАКАЗ]            │
└─────────────────────────────────────────────────────────┘
```

### 20.3 Генерация nest (раскладки)

**Алгоритм:**
```python
async def generate_rework_nest(
    order_items: list[tuple[str, int]],  # [(sku, qty), ...]
    sidra_name: str,
    project_id: int,
    system_scope: Any,
) -> WorkItem:
    """
    1. Группирует детали по материалу+толщине
    2. Для каждой группы создаёт nest (раскладку)
    3. Сохраняет GNC файлы в папку rework/<sidra_name>/
    4. Регистрирует WorkItem + TaskItems
    """
    
    # 1. Загрузить детали из PartLibrary
    parts_by_material: dict[tuple[str, float], list[PartLibrary]] = {}
    for sku, qty in order_items:
        part = session.exec(select(PartLibrary).where(PartLibrary.sku == sku)).first()
        if part and part.mat_type_id:
            mat = session.get(MaterialType, part.mat_type_id)
            key = (mat.code, mat.thickness or 0)
            parts_by_material.setdefault(key, []).append((part, qty))
    
    # 2. Для каждого материала — создать nest
    task_items = []
    for (mat_code, thickness), parts in parts_by_material.items():
        # Наивный nest: размещаем детали по сетке на стандартном листе
        sheet_x, sheet_y = get_standard_sheet_size(mat_code)
        
        nest_gnc = generate_naive_nest_gnc(parts, sheet_x, sheet_y)
        
        # Сохранить GNC
        gnc_path = f"rework/{sidra_name}/Sheet_{mat_code}_{thickness}.GNC"
        save_gnc_file(nest_gnc, gnc_path)
        
        # 3. Создать TaskItem
        task = TaskItem(
            work_item_id=work_item.id,  # будет создан ниже
            file_name=f"Sheet_{mat_code}_{thickness}.GNC",
            file_path=gnc_path,
            mat_type_id=parts[0][0].mat_type_id,
            thickness=thickness,
            sheet_x=sheet_x,
            sheet_y=sheet_y,
            sheet_qty=calculate_required_sheets(parts, sheet_x, sheet_y),
            status=TaskItemStatus.PLANNED,
        )
        task_items.append(task)
    
    # 4. Создать WorkItem (Sidra)
    work_item = WorkItem(
        project_id=project_id,
        folder_name=sidra_name,
        folder_path=f"rework/{sidra_name}/",
        status=WorkItemStatus.NEW,
    )
    session.add(work_item)
    session.flush()
    
    # Привязать TaskItems к WorkItem
    for task in task_items:
        task.work_item_id = work_item.id
        session.add(task)
    
    session.commit()
    
    # 5. Запустить сканер на новую папку
    # (или добавить вручную в базу — bypass scanner)
    
    return work_item
```

**Наивный nest:**
- Стандартный лист (например 3000×1500 мм)
- Детали размещаются по сетке (grid layout)
- Поворот деталей для оптимизации (если bbox_x < bbox_y — повернуть)
- Проверка пересечений (простая AABB)

**Папка rework:**
```
rework/
├── REWORK-001/
│   ├── Sheet_ST37-2_4.0.GNC
│   └── Sheet_S235_5.0.GNC
├── REWORK-002/
│   └── Sheet_SS1.4003_1.5.GNC
```

### 20.4 Файлы

- `src/docuflow/features/parts/order_cart.py` — OrderCart (сессионная корзина)
- `src/docuflow/features/parts/rework_generator.py` — генерация nest + WorkItem
- `src/docuflow/lib/widgets/order_cart_panel.py` — UI панель корзины

## 21. Финальные критерии приёмки

### Обязательные (все)
- [ ] `TaskItemStatus.SUSPENDED` — длительная приостановка
- [ ] Авто-расчёт `qty_produced` из TaskPart.qty * sheets_done
- [ ] Диалог завершения: "Создать новую паллету" / "Добавить к существующей"
- [ ] Связь TaskItem ↔ ProductionUnit с обратным поиском
- [ ] Показ номера паллеты в TaskItemRow (DONE) и TaskGroupRow
- [ ] Поиск паллет по project/work_item/task_id и обратно
- [ ] Резервирование материала при назначении на узел
- [ ] Авто-списание материала при DONE
- [ ] **Part Library: клик на деталь в TaskItem → модальное окно с превью + список задач**
- [ ] **Part Library: кнопка "Показать в производстве" с фильтром по SKU**
- [ ] **Warehouse: резервирование материала прямо из Task Board (модальное окно)**
- [ ] **Warehouse: новая вкладка "РЕЗЕРВЫ" с привязкой к нарядам**
- [ ] **Production: обратный поиск по label_id в Omnisearch**
- [ ] **Production: deeplink из паллеты в Task Board**
- [ ] **Chat: тип HANDOVER, deeplink #<task_id>, канал "Производство"**
- [ ] **Incidents: deeplink на TaskItem, фильтр по Project/WorkItem**
- [ ] **Analytics: метрики TaskGroup, node_utilization, pallet_by_project**
- [ ] **Reports: data blocks task_group_summary, material_reservation, pallet_by_project**
- [ ] **Модальные окна: Project, WorkItem, TaskGroup, TaskItem, Pallet с полным просмотром/редактированием**
- [ ] **Превью неста у TaskItem: SVG раскладка деталей на листе**
- [ ] **Part Library: корзина заказа деталей с количеством**
- [ ] **Part Library: генерация rework nests по материалам + регистрация WorkItem**

### Файлы (итоговый список)
- `src/docuflow/domain/entities/production.py` — TaskGroup, ViewState, ViewPreset, SUSPENDED
- `src/docuflow/features/task_board/task_group_service.py` — замена BatchEngine
- `src/docuflow/features/task_board/view.py` — единый Task Board (2 таба)
- `src/docuflow/lib/widgets/hierarchy_table.py` — древовидная таблица
- `src/docuflow/lib/widgets/hierarchy_row.py` — двухстрочная строка
- `src/docuflow/lib/widgets/filter_panel.py` — фильтры с пресетами
- `src/docuflow/lib/widgets/handover_form.py` — форма передачи смены
- `src/docuflow/lib/widgets/handover_banner.py` — баннер входящей смены
- `src/docuflow/lib/widgets/nest_preview.py` — превью неста SVG
- `src/docuflow/lib/widgets/order_cart_panel.py` — панель корзины Part Library
- `src/docuflow/features/parts/order_cart.py` — OrderCart
- `src/docuflow/features/parts/rework_generator.py` — генерация nest + WorkItem
