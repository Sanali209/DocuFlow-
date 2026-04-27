# Дизайн-документ: Task Board v2.0 — Единый иерархический вид

## 1. Цель

Упорядочить понятия Project → WorkItem (Sidra) → TaskGroup → TaskItem и создать единый иерархический Task Board, доступный и оператору, и бригадиру. Убрать дублирование вкладок, устранить путаницу с "батчами".

## 2. Терминология

| Термин | Определение |
|--------|-------------|
| **Project** | Проект/контракт (например "SHLAV-2"). Верхний уровень иерархии. |
| **WorkItem** | Наряд (папка с файлами), ранее "Sidra". Содержит TaskItems. |
| **TaskGroup** | Группа задач (ранее "batch"). НЕ имеет собственного статуса. Статус группы = агрегация статусов вложенных задач. |
| **TaskItem** | Отдельный GNC-файл (задача резки). Имеет статус, прогресс, назначенный узел. |

## 3. Иерархия данных

```
Project
└── WorkItem (Sidra/Наряд)
    └── TaskGroup (ранее Batch)
        └── TaskItem (GNC задача)
```

**Правила:**
- TaskGroup — любая группа задач, нет ограничений на состав.
- Helper-методы группировки по материалу+толщине создают TaskGroup, но бригадир может группировать вручную.
- Статус TaskGroup вычисляется: `IN_PROGRESS` если хоть одна задача в работе; `DONE` если все DONE; `PLANNED` если все PLANNED; иначе `MIXED`.

## 4. Единый вид Task Board

### 4.1 Табы (для всех ролей)

| Таб | Содержимое |
|-----|-----------|
| **Производство** | Древовидная таблица: Project → WorkItem → TaskGroup → TaskItem |
| **Моя корзина** | TaskGroup'ы, назначенные на текущий узел (только оператор) |
| **Передача смены** | Форма передачи смены + входящие заметки |

### 4.2 Роль оператора

Оператор видит ТОЛЬКО узлы, привязанные к его рабочему месту.
- В табе "Производство" — раскрывающиеся WorkItems, но только TaskGroup'ы, назначенные на его узел.
- В табе "Моя корзина" — только его TaskGroup'ы с кнопками управления.

### 4.3 Роль бригадира

Бригадир видит ВСЕ узлы и ВСЕ задачи.
- В табе "Производство" — полная иерархия.
- Может назначать TaskGroup на узлы (drag-and-drop или кнопка).
- Может создавать/разбивать TaskGroup'ы.

## 5. TaskGroup entity

```python
class TaskGroup(BaseEntity, table=True):
    name: str | None = None  # auto: "ST37-2 4.0mm (3 задачи)" или ручное
    work_item_id: int = Field(foreign_key="workitem.id")
    created_by: str | None = None  # "system" или username
    grouping_rule: str = Field(default="manual")  # "manual" | "auto_material"
    
    # Relations
    work_item: WorkItem | None = Relationship(back_populates="task_groups")
    tasks: list["TaskItem"] = Relationship(back_populates="task_group")
```

**Migration:**
- `TaskItem.batch_group_id` (str UUID) → `TaskItem.task_group_id` (int FK)
- `WorkerBucketEntry.batch_group_id` → `WorkerBucketEntry.task_group_id`
- Существующие UUID-батчи конвертируются в TaskGroup записи.

## 6. Единая иерархическая таблица

```
├─ ▼ SHLAV-2 (Project)
│  ├─ ▼ 3455-11-144 (WorkItem)
│  │  ├─ ▶ ST37-2 4.0mm [3 задачи] [🔥 В работе]
│  │  └─ ▶ S235 5.0mm [2 задачи] [⏳ Ожидание]
│  └─ ▼ 3455-11-145 (WorkItem)
│     └─ ▶ ST37-2 6.0mm [1 задача] [✅ Готово]
```

Раскрытие уровня показывает детали:
- WorkItem: список файлов, статус, дата
- TaskGroup: список TaskItems с прогрессом, материалом
- TaskItem: кнопки Старт/Пауза/Доне, прогресс-бар, sheets_done

## 7. Передача смены

**Форма отправки:**
- Поле "Кому передаёте" (строка)
- Поле "Заметка" (textarea)
- Кнопка "Передать смену"

**Входящее сообщение:**
- При выборе узла: если есть `handover_note` для текущего пользователя — показывается баннер.
- Баннер: текст заметки + кнопка "Принято".
- "Принято" скрывает баннер и создаёт WorkLog(HANDOVER_ACCEPTED).

**Сохранение:**
- `WorkerBucketEntry.assigned_user` меняется.
- `WorkerBucketEntry.handover_from`, `handover_note`, `handover_at` заполняются.
- Создаётся `WorkLog(HANDOVER)` + `ChatMessage` (опционально).

## 8. Отказ от старых сущностей

- Удалить `batch_engine.py` (BatchEngine, BatchRule, BatchGroup dataclasses).
- Заменить на `TaskGroupService` с методами:
  - `auto_group_by_material(work_item_id)` — группировка по материалу+толщине
  - `create_manual_group(task_ids, name=None)` — ручная группировка
  - `move_task_to_group(task_id, group_id)` — перемещение между группами
  - `split_group(group_id, task_ids)` — разделение группы
  - `get_group_status(group)` — агрегация статуса

## 9. UI-компоненты

| Компонент | Назначение |
|-----------|-----------|
| `TaskGroupRow` | Строка TaskGroup с агрегированным статусом и прогрессом |
| `TaskItemRow` | Строка задачи с кнопками действий и прогресс-баром |
| `HierarchyTable` | Древовидная таблица с раскрытием уровней |
| `HandoverBanner` | Баннер входящей передачи смены |
| `HandoverForm` | Форма передачи смены |

## 10. Миграция данных

1. Создать таблицу `taskgroup`.
2. Для каждого уникального `TaskItem.batch_group_id` создать `TaskGroup`.
3. Заполнить `TaskItem.task_group_id` FK.
4. Обновить `WorkerBucketEntry.task_group_id`.
5. Удалить колонку `TaskItem.batch_group_id`.
6. Удалить `BatchEngine` и `batch_engine.py`.

## 11. Критерии приёмки

- [ ] Оператор видит TaskGroup'ы на своём узле в табе "Моя корзина"
- [ ] Бригадир видит иерархию Project→WorkItem→TaskGroup→TaskItem
- [ ] TaskGroup можно создать вручную или авто-группировкой по материалу
- [ ] Передача смены: форма отправки + баннер входящего + кнопка Принято
- [ ] Старый `batch_group_id` удалён, `TaskGroup` — полноценная сущность
- [ ] Нет разделения "бригадир видит одно, оператор другое" — оба видят один UI с разной фильтрацией
