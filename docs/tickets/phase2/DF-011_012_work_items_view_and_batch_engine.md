# DF-011: work_items/view.py

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 2 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-010](./DF-010_work_item_system.md), [DF-015](./DF-015_view_preset.md), [DF-016](./DF-016_core_widgets.md) |
| **Блокирует** | Gate 2 |

---

## Контекст

Главный экран бригадира. Список нарядов с фильтрацией. Карточка наряда с деталями, логом и кнопками действий.

---

## Подзадачи

- [ ] `work_items/view.py` — основной view:
  - [ ] 🔽 Фильтр панель: статус (multi), тип, проект, дата, строка поиска
  - [ ] 📋 Таблица нарядов (WorkItemTable):
    - Колонки: статус badge, folder_name, sidra_number, тип, проект, doc_received_at, taskitem count, кнопки
    - Строка: двойной клик → открыть карточку
    - Статус badge: цветной (NEW=blue, PENDING=orange, REGISTERED=green, ...)
  - [ ] ViewPreset вкладки (из DF-015): "Все" / "Мои незакрытые" / "Сегодня"
  - [ ] **Карточка WorkItem** (modal или side panel):
    - Заголовок: folder_name + статус badge
    - Секция: sidra_number, sidra_step, doc_date, project
    - Кнопки: "📂 Открыть в Explorer", "✅ Зарегистрировать документ", "🔒 Заблокировать"
    - Таблица TaskItem: step_index, mat_type, sheet_qty, status, estimated_minutes
    - Клик на TaskItem → превью SVG детали (из PartPreview виджет)
    - PartTemplate предупреждения (если есть)
    - WorkLog лента (хронология)

- [ ] `lib/widgets/work_item_card.py` — переиспользуемый виджет карточки
- [ ] `lib/widgets/status_badge.py` — цветные бейджи:
  - NEW=blue, PENDING_CUTS=orange, REGISTERED=teal, IN_PROGRESS=green
  - ON_HOLD=yellow, BLOCKED=red, DONE=gray, CANCELLED=darkgray

---

## Псевдокод

```python
# work_items/view.py

class WorkItemsView:
    def render(self):
        with ui.column():
            self._render_filter_bar()
            ViewPresetSwitcher(module="work_items").render()
            self._render_table()
    
    def _render_table(self):
        items = self.system.list(self.active_filters)
        with ui.table(rows=items) as t:
            t.add_column("status", label="Статус",
                         cell=lambda r: StatusBadge(r.status))
            t.add_column("folder_name", label="Папка")
            t.add_column("sidra_number", label="Наряд №")
            t.add_column("taskitem_count", label="Нест-файлов")
            t.add_column("actions", label="",
                         cell=lambda r: ui.button("📂", on_click=lambda: 
                             self.system.open_in_explorer(r.id)))
        t.on_row_click(lambda r: self._show_card(r))
    
    def _show_card(self, work_item: WorkItem):
        with ui.dialog() as d, ui.card():
            WorkItemCard(work_item, self.system).render()
        d.open()
```

---

## TDD: Тесты

```python
async def test_view_renders_without_error(mock_sdk):
    view = WorkItemsView(sdk=mock_sdk)
    await view.render()  # smoke test

def test_status_badge_colors():
    badge = StatusBadge(WorkItemStatus.PENDING_CUTS)
    assert badge.color == "orange"
    badge2 = StatusBadge(WorkItemStatus.DONE)
    assert badge2.color == "gray"
```

---

## Definition of Done

```
✓ Таблица нарядов рендерится с данными
✓ Фильтр по статусу работает
✓ Двойной клик → карточка открывается
✓ "Зарегистрировать документ" → WorkItem.status меняется в UI
✓ "📂 Открыть в Explorer" — работает (вызывает explorer.exe)
✓ WorkLog лента показывает историю
✓ SVG превью детали рендерится (не вылетает)
✓ ViewPreset "Мои незакрытые" применяет фильтр
```

---

# DF-012: BatchEngine + BatchRule

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 2 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md) |
| **Блокирует** | [DF-013](./DF-013_task_board_system.md) |

---

## Контекст

BatchEngine автоматически группирует TaskItem по общим параметрам материала для оптимизации переналадки станка. Результат — `batch_group_id` (UUID) на связанных TaskItem. Бригадир может ручную редактировать батчи.

---

## Подзадачи

- [ ] `BatchRule` dataclass:
  - `group_by: list[str]` = `["mat_type_id", "thickness", "sheet_x", "sheet_y"]`
  - `include_other_work_items: bool` = True (можно добавить из других нарядов)
  - `max_batch_size: int` = None (без ограничения)
- [ ] `BatchEngine`:
  - `compute(tasks: list[TaskItem], rule: BatchRule) -> list[BatchGroup]`
  - Группировка: `itertools.groupby` по ключу из rule.group_by
  - Каждая группа → новый `batch_group_id = uuid4()`
  - `BatchGroup`: `batch_group_id, tasks[], mat_type, total_sheets, estimated_minutes`
- [ ] `apply_batches(groups: list[BatchGroup], session)`:
  - Обновить `task_item.batch_group_id` для каждого таска
- [ ] Проверка STOCK_ALERT:
  - Для каждого TaskPart: проверить PartLibrary + ProductionUnit where is_stock=True
  - Если деталь есть в запасе → `WorkLog(STOCK_ALERT)` + `ChatMessage(WARNING)`
- [ ] Ручное изменение батча:
  - `move_task(task_id, new_batch_group_id)` → обновить batch_group_id
  - `create_batch(task_ids)` → новый batch_group_id для списка
  - `split_batch(batch_group_id, task_ids_to_separate)` → создать новый батч для подмножества

---

## Псевдокод

```python
class BatchEngine:
    
    def compute(self, tasks: list[TaskItem], rule: BatchRule) -> list[BatchGroup]:
        """
        Группирует задачи по критериям материала.
        Порядок внутри батча: по step_index, batch_index.
        """
        def key_fn(t: TaskItem) -> tuple:
            return tuple(getattr(t, field, None) for field in rule.group_by)
        
        sorted_tasks = sorted(tasks, key=key_fn)
        groups = []
        for key, task_group in itertools.groupby(sorted_tasks, key=key_fn):
            task_list = sorted(list(task_group), 
                               key=lambda t: (t.step_index or 0, t.batch_index or 0))
            batch_id = uuid4()
            groups.append(BatchGroup(
                batch_group_id=batch_id,
                tasks=task_list,
                mat_type_id=task_list[0].mat_type_id,
                total_sheets=sum(t.sheet_qty or 0 for t in task_list),
                estimated_minutes=sum(t.estimated_minutes or 0 for t in task_list)
            ))
        return groups
    
    def check_stock_alerts(self, tasks: list[TaskItem], session) -> list[StockAlert]:
        """Проверяет является ли деталь уже в is_stock ProductionUnit."""
        alerts = []
        for task in tasks:
            for part in task.task_parts:
                in_stock = session.exec(
                    select(ProductionUnit)
                    .where(ProductionUnit.task_item.has(
                        TaskItem.task_parts.any(TaskPart.part_sku == part.part_sku)))
                    .where(ProductionUnit.is_stock == True)
                ).all()
                if in_stock:
                    alerts.append(StockAlert(sku=part.part_sku, units=in_stock))
        return alerts
```

---

## TDD: Тесты

```python
def test_batch_groups_by_material(in_memory_db):
    """Задачи с одним материалом → один батч."""
    mat = MaterialType(id=1, code="ST37", thickness=3.0, sheet_x=3000, sheet_y=1500)
    tasks = [TaskItem(mat_type_id=1, ...) for _ in range(3)]
    
    engine = BatchEngine()
    groups = engine.compute(tasks, BatchRule())
    assert len(groups) == 1
    assert len(groups[0].tasks) == 3

def test_different_materials_separate_batches():
    tasks = [
        TaskItem(mat_type_id=1, thickness=3.0, ...),
        TaskItem(mat_type_id=2, thickness=2.0, ...),
    ]
    groups = BatchEngine().compute(tasks, BatchRule())
    assert len(groups) == 2

def test_task_sorted_by_step_batch_index():
    tasks = [
        TaskItem(step_index=2, batch_index=1, mat_type_id=1, ...),
        TaskItem(step_index=1, batch_index=1, mat_type_id=1, ...),
        TaskItem(step_index=1, batch_index=2, mat_type_id=1, ...),
    ]
    group = BatchEngine().compute(tasks, BatchRule())[0]
    steps = [(t.step_index, t.batch_index) for t in group.tasks]
    assert steps == [(1,1), (1,2), (2,1)]  # sorted
```

---

## Definition of Done

```
✓ compute() группирует по mat_type + thickness + sheet_x + sheet_y
✓ Порядок внутри батча: step_index → batch_index
✓ apply_batches() присваивает batch_group_id в БД
✓ check_stock_alerts() возвращает STOCK_ALERT при is_stock деталях
✓ move_task(), create_batch(), split_batch() работают
✓ Все тесты проходят
```
