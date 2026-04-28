# TDD План реализации: доведение Task Board v2 до 100% соответствия спеке

**Дата:** 2026-04-28  
**Цель:** Закрыть все пробелы из compliance-отчёта.  
**Методология:** Test-Driven Development (TDD) — красный тест → минимальный код → зелёный тест → рефакторинг.  
**Качество:** После КАЖДОГО изменения — `ruff check --fix`, `ruff format`, `pyright`.

---

## 0. Правила работы с кодовой базой (ИНСАЙДЫ)

### 0.1 DI-контейнер: Scope.APP vs Scope.REQUEST
```python
# src/docuflow/infrastructure/di.py
@provide(scope=Scope.APP)   # ← singleton, живёт всё время работы приложения
@provide(scope=Scope.REQUEST)  # ← новый инстанс на каждый HTTP-запрос/ui-тик
```
**Правило:** НЕ используй `Session` из `Scope.APP` провайдеров. Всё, что пишет в БД из background loops, использует `Session(self.db_engine)` напрямую. Всё, что рендерит UI, использует `async with self.scope() as req: session = await req.get(Session)`.

### 0.2 Async vs Sync
```python
# NiceGUI рендеринг — async
async def render(self): ...

# Background loops (scanner, orchestrator) — async
async def _discovery_loop(self): ...

# Domain methods (чистая логика) — sync
def get_group_status(self, group): ...
```
**Правило:** Не вызывай `await` из sync-методов. Если нужно — используй `asyncio.get_event_loop().create_task(...)`.

### 0.3 SQLModel Session lifecycle
```python
# Правильно: with Session(self.db_engine) as session:
with Session(self.db_engine) as session:
    item = session.get(Item, id)
    item.name = "new"
    session.commit()

# Неправильно: объект, созданный в одной сессии, используется в другой
with Session(self.db_engine) as s1:
    item = s1.get(Item, id)
with Session(self.db_engine) as s2:
    s2.add(item)  # ← DetachedInstanceError!
```

### 0.4 Session в UI-рендеринге
```python
async with self.scope() as req:
    session = await req.get(Session)
    tb_system = await req.get(TaskBoardSystem)
    # session управляется контейнером, НЕ коммить вручную!
    # Не используй session.commit() в render()!
```

### 0.5 FileBus: атомарная запись
```python
# Всегда через TEMP_ + rename
await self._atomic_write(self._inbox, filename, payload)
```

### 0.6 HMAC signing: ключи должны быть отсортированы
```python
json.dumps(data, sort_keys=True)  # Обязательно sort_keys!
```

### 0.7 PollingObserver (не стандартный Observer)
```python
from watchdog.observers.polling import PollingObserver
# Стандартный Observer не работает через Samba/CIFS
```

### 0.8 Async тесты с SQLite
```python
# sqlite:///:memory: + StaticPool для async тестов
# Временные файлы вызывают "database is locked"
```

### 0.9 Русский язык в UI
- Все метки, заголовки, кнопки — на русском
- Docstrings — русский или английский (смешанно OK)
- Переменные/классы — английский

### 0.10 Структура новых файлов
```
src/docuflow/lib/widgets/<widget>.py      # UI-компоненты
tests/unit/<area>/test_<module>.py        # Unit тесты
tests/ui/test_<widget>.py                 # UI smoke tests
```
**Правило:** Не создавай файлы в корне проекта. Всё через `src/` или `tests/`.

---

## 1. Фаза 1: ViewState — сохранение раскрытия иерархии

### Задача
`ViewState` entity существует, но `HierarchyTable` использует хардкод `is_expanded=True/False`. Нужно:
1. Загружать состояние из БД при рендеринге
2. Сохранять при клике toggle
3. Удалять при сворачивании

### TDD
1. **Красный тест** `tests/unit/test_view_state.py`:
```python
def test_view_state_save_and_load(session):
    from docuflow.domain.entities.production import ViewState
    vs = ViewState(user_id="u1", view_name="task_board", entity_type="project", entity_id="1", is_expanded=True)
    session.add(vs); session.commit()
    loaded = session.exec(select(ViewState).where(ViewState.user_id == "u1")).first()
    assert loaded.is_expanded is True
```
2. **Красный тест** `tests/ui/test_hierarchy_table.py`:
```python
async def test_hierarchy_table_uses_viewstate(system_scope):
    table = HierarchyTable(user_id="u1", view_name="task_board", system_scope=system_scope)
    # Проверить что is_expanded берётся из ViewState, а не хардкод
```
3. **Минимальный код** в `HierarchyTable.__init__` / `render()`:
   - Добавить `ViewStateRepository` (или inline queries)
   - При `_render_project` загружать `is_expanded` из `ViewState`
   - При toggle — `upsert` в `ViewState`
4. **Зелёный** → рефакторинг → линтеры.

### Файлы
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py`
- Modify: `src/docuflow/lib/widgets/hierarchy_row.py` (callback toggle)
- Create: `tests/unit/test_view_state.py`
- Modify: `tests/ui/test_hierarchy_table.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/lib/widgets/hierarchy_table.py src/docuflow/lib/widgets/hierarchy_row.py tests/unit/test_view_state.py
uv run ruff format src/docuflow/lib/widgets/hierarchy_table.py src/docuflow/lib/widgets/hierarchy_row.py tests/unit/test_view_state.py
uv run pyright src/docuflow/lib/widgets/hierarchy_table.py
```

---

## 2. Фаза 2: FilterPanel — комплексные фильтры и пресеты

### Задача
Создать `FilterPanel` widget + интеграция в `HierarchyTable`.  
Фильтры: Project, WorkItem status, TaskGroup status, TaskItem status, Node, Material, Thickness, Date range, Urgent only.

### TDD
1. **Красный тест** `tests/ui/test_filter_panel.py`:
```python
def test_filter_panel_renders():
    panel = FilterPanel(on_apply=lambda f: None, system_scope=None)
    assert panel is not None
```
2. **Красный тест** `tests/unit/test_task_board_system.py`:
```python
def test_get_hierarchy_with_filters(session, system):
    # Создать Project, WorkItem, TaskItem
    # Применить filter={"project_id": 1}
    # Проверить что вернулся только 1 проект
```
3. **Минимальный код**:
   - `FilterPanel` — `ui.row()` с `ui.select`, `ui.number`, `ui.input`, `ui.date`, `ui.checkbox`
   - `HierarchyTable` — передавать `filters` в SQL queries
   - `TaskBoardSystem.get_hierarchy(filters)` — строит SQL с `where` clauses
4. **Зелёный** → рефакторинг → линтеры.

### Файлы
- Create: `src/docuflow/lib/widgets/filter_panel.py`
- Create: `tests/ui/test_filter_panel.py`
- Modify: `src/docuflow/features/task_board/view.py` (вставить FilterPanel над таблицей)
- Modify: `src/docuflow/features/task_board/system.py` (добавить `get_hierarchy`)
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py` (принимать filters)

### Линтеры
```bash
uv run ruff check --fix src/docuflow/lib/widgets/filter_panel.py src/docuflow/features/task_board/system.py src/docuflow/features/task_board/view.py
uv run ruff format src/docuflow/lib/widgets/filter_panel.py src/docuflow/features/task_board/system.py src/docuflow/features/task_board/view.py
uv run pyright src/docuflow/lib/widgets/filter_panel.py src/docuflow/features/task_board/system.py
```

---

## 3. Фаза 3: ViewPreset — сохранение/загрузка пресетов фильтров

### Задача
ViewPreset entity уже создана. Нужен UI для сохранения и выбора пресетов.

### TDD
1. **Красный тест** `tests/unit/test_view_preset.py`:
```python
def test_save_and_load_preset(session):
    preset = ViewPreset(name="Мои срочные", user_id="u1", view_name="task_board", filters_json='{"urgent": true}')
    session.add(preset); session.commit()
    loaded = session.get(ViewPreset, preset.id)
    assert loaded.filters_json == '{"urgent": true}'
```
2. **Красный тест** `tests/ui/test_filter_panel.py`:
```python
def test_filter_panel_save_preset():
    panel = FilterPanel(on_apply=lambda f: None, system_scope=None)
    # Проверить наличие кнопки "Сохранить пресет"
```
3. **Минимальный код**:
   - `FilterPanel` — добавить `ui.select` для выбора пресета + кнопку "💾 Сохранить"
   - `AdminSystem` или `ViewPresetSystem` — методы `save_preset`, `get_presets`
4. **Зелёный** → линтеры.

### Файлы
- Modify: `src/docuflow/lib/widgets/filter_panel.py`
- Create/Modify: `src/docuflow/features/task_board/view_preset_system.py` (если нет)
- Create: `tests/unit/test_view_preset.py`
- Modify: `tests/ui/test_filter_panel.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/lib/widgets/filter_panel.py tests/unit/test_view_preset.py
uv run ruff format src/docuflow/lib/widgets/filter_panel.py tests/unit/test_view_preset.py
uv run pyright src/docuflow/lib/widgets/filter_panel.py
```

---

## 4. Фаза 4: Part Library ↔ Task Board deeplink

### Задача
1. В `TaskItemRow` (DONE/любой статус) показывать список деталей с кликабельными SKU
2. Клик на SKU → модальное окно с `PartPreview` + список задач с этой деталью
3. В `PartLibraryView` добавить кнопку "Показать в производстве"

### TDD
1. **Красный тест** `tests/ui/test_hierarchy_table.py`:
```python
async def test_taskitem_row_shows_part_skus(system_scope):
    # Создать TaskItem с TaskPart
    # Проверить что в строке есть кликабельный SKU
```
2. **Красный тест** `tests/ui/test_part_library_view.py`:
```python
def test_part_library_has_show_in_production_button():
    # Проверить наличие кнопки
```
3. **Минимальный код**:
   - `hierarchy_table.py` `_render_taskitem` — добавить строку с деталями
   - `entity_modals.py` или inline — `PartDetailModal` (или использовать `TaskItemModal`)
   - `parts/view.py` — кнопка "Показать в производстве" → `ui.navigate("/task_board?sku=BASE-001")`
4. **Зелёный** → линтеры.

### Файлы
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py`
- Create/Modify: `src/docuflow/lib/widgets/part_detail_modal.py`
- Modify: `src/docuflow/features/parts/view.py`
- Modify: `tests/ui/test_hierarchy_table.py`
- Create: `tests/ui/test_part_library_view.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/lib/widgets/hierarchy_table.py src/docuflow/features/parts/view.py
uv run ruff format src/docuflow/lib/widgets/hierarchy_table.py src/docuflow/features/parts/view.py
uv run pyright src/docuflow/lib/widgets/hierarchy_table.py src/docuflow/features/parts/view.py
```

---

## 5. Фаза 5: Incidents — deeplink на TaskItem + фильтры

### Задача
1. Сделать `task_item_id` в incident кликабельной ссылкой → Task Board
2. Добавить фильтры по Project/WorkItem

### TDD
1. **Красный тест** `tests/ui/test_incident_view.py`:
```python
def test_incident_card_shows_clickable_task_link():
    # Проверить что ui.link присутствует
```
2. **Минимальный код**:
   - `features/chat/incident_view.py` — заменить `ui.label(f"Task: {id}")` на `ui.link(f"#{id}", f"/task_board?task_id={id}")`
   - Добавить `ui.select` для фильтра по Project и WorkItem
3. **Зелёный** → линтеры.

### Файлы
- Modify: `src/docuflow/features/chat/incident_view.py`
- Create: `tests/ui/test_incident_view.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/features/chat/incident_view.py
uv run ruff format src/docuflow/features/chat/incident_view.py
uv run pyright src/docuflow/features/chat/incident_view.py
```

---

## 6. Фаза 6: Chat — канал "Производство"

### Задача
Добавить канал "Производство" с авто-сообщениями (завершённые задачи, резервирования).

### TDD
1. **Красный тест** `tests/ui/test_chat_view.py`:
```python
def test_chat_has_production_channel():
    # Проверить что канал "Производство" есть в списке
```
2. **Минимальный код**:
   - `features/chat/view.py` — добавить `"production": "Производство"` в список каналов
   - В `TaskBoardSystem.complete_task()` — публиковать `ChatMessage(HANDOVER, ...)` или новый тип `AUTO`
3. **Зелёный** → линтеры.

### Файлы
- Modify: `src/docuflow/features/chat/view.py`
- Modify: `src/docuflow/features/task_board/system.py`
- Create: `tests/ui/test_chat_view.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/features/chat/view.py src/docuflow/features/task_board/system.py
uv run ruff format src/docuflow/features/chat/view.py src/docuflow/features/task_board/system.py
uv run pyright src/docuflow/features/chat/view.py src/docuflow/features/task_board/system.py
```

---

## 7. Фаза 7: Pallet search by project (`find_pallets_by_project`)

### Задача
Добавить недостающий метод в `TaskBoardSystem`.

### TDD
1. **Красный тест** `tests/unit/features/test_task_board_system.py`:
```python
def test_find_pallets_by_project(session, system):
    # Создать Project → WorkItem → TaskItem → ProductionUnit
    # system.find_pallets_by_project(project.id, session)
    # assert len(pallets) == 1
```
2. **Минимальный код** в `task_board/system.py`:
```python
def find_pallets_by_project(self, project_id: int, session: Session) -> list[ProductionUnit]:
    return list(session.exec(
        select(ProductionUnit).join(TaskItem).join(WorkItem).where(WorkItem.project_id == project_id)
    ).all())
```
3. **Зелёный** → линтеры.

### Файлы
- Modify: `src/docuflow/features/task_board/system.py`
- Modify: `tests/unit/features/test_task_board_system.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/features/task_board/system.py tests/unit/features/test_task_board_system.py
uv run ruff format src/docuflow/features/task_board/system.py tests/unit/features/test_task_board_system.py
uv run pyright src/docuflow/features/task_board/system.py
```

---

## 8. Фаза 8: Analytics `pallet_by_project` metric

### Задача
Добавить метрику в `analytics/system.py`.

### TDD
1. **Красный тест** `tests/unit/features/test_analytics.py`:
```python
def test_pallet_by_project_metric(session, system):
    # Создать паллеты для разных проектов
    # metrics = system.calculate_metrics(session)
    # assert metrics["pallet_by_project"]["SHLAV-2"] == 2
```
2. **Минимальный код** в `analytics/system.py`.
3. **Зелёный** → линтеры.

### Файлы
- Modify: `src/docuflow/features/analytics/system.py`
- Modify: `tests/unit/features/test_analytics.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/features/analytics/system.py tests/unit/features/test_analytics.py
uv run ruff format src/docuflow/features/analytics/system.py tests/unit/features/test_analytics.py
uv run pyright src/docuflow/features/analytics/system.py
```

---

## 9. Фаза 9: Complete dialog — выбор "новая паллета" vs "существующая"

### Задача
Сейчас `complete_task(task_id, create_pallet=True)` просто создаёт паллету. Нужен UI-диалог.

### TDD
1. **Красный тест** `tests/ui/test_complete_dialog.py`:
```python
def test_complete_dialog_shows_pallet_options():
    dialog = CompleteTaskDialog(task_id=1, system_scope=None)
    # Проверить наличие radio-кнопок
```
2. **Минимальный код**:
   - `CompleteTaskDialog` widget (или inline в `hierarchy_table.py`)
   - Radio: "Создать новую" / "Добавить к существующей [выбор ▼]"
   - При "Добавить" — `existing_pallet.qty_produced += qty`
3. **Зелёный** → линтеры.

### Файлы
- Create: `src/docuflow/lib/widgets/complete_task_dialog.py`
- Create: `tests/ui/test_complete_dialog.py`
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py` (заменить прямой вызов на диалог)

### Линтеры
```bash
uv run ruff check --fix src/docuflow/lib/widgets/complete_task_dialog.py src/docuflow/lib/widgets/hierarchy_table.py
uv run ruff format src/docuflow/lib/widgets/complete_task_dialog.py src/docuflow/lib/widgets/hierarchy_table.py
uv run pyright src/docuflow/lib/widgets/complete_task_dialog.py
```

---

## 10. Фаза 10: Reservation при назначении на узел

### Задача
`assign_task_group_to_node()` должен автоматически создавать резерв материала.

### TDD
1. **Красный тест** `tests/unit/features/test_task_board_system.py`:
```python
def test_assign_task_group_creates_reservation(session, system, inventory_system):
    # Создать TaskGroup с TaskItem (mat_type_id=1, sheet_qty=5)
    # system.assign_task_group_to_node(tg.id, "LASER_1", session)
    # Проверить что Reservation создана на 5 листов
```
2. **Минимальный код** в `task_board/system.py`:
   - После `task.assigned_to_node = node_id` добавить вызов `inventory.create_reservation(...)`
   - Нужен `estimated_sheets = sum(t.sheet_qty for t in tg.tasks)`
3. **Зелёный** → линтеры.

### Файлы
- Modify: `src/docuflow/features/task_board/system.py`
- Modify: `tests/unit/features/test_task_board_system.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/features/task_board/system.py
uv run ruff format src/docuflow/features/task_board/system.py
uv run pyright src/docuflow/features/task_board/system.py
```

---

## 11. Фаза 11: "Создать инцидент" в TaskItemRow

### Задача
Добавить кнопку "⚠️" в `TaskItemRow`, которая создаёт инцидент.

### TDD
1. **Красный тест** `tests/ui/test_hierarchy_table.py`:
```python
def test_taskitem_row_has_create_incident_button():
    # Проверить наличие кнопки/иконки
```
2. **Минимальный код**:
   - `hierarchy_table.py` `_render_taskitem` — добавить `("⚠️ Инцидент", partial(self._create_incident, task.id))`
   - `_create_incident` — вызов `IncidentSystem.create_incident(task_item_id=...)`
3. **Зелёный** → линтеры.

### Файлы
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py`
- Modify: `tests/ui/test_hierarchy_table.py`

### Линтеры
```bash
uv run ruff check --fix src/docuflow/lib/widgets/hierarchy_table.py
uv run ruff format src/docuflow/lib/widgets/hierarchy_table.py
uv run pyright src/docuflow/lib/widgets/hierarchy_table.py
```

---

## 12. Итоговая проверка

После завершения всех фаз:

```bash
# Unit tests
uv run pytest tests/unit/ -q

# UI tests (исключая pre-existing broken)
uv run pytest tests/ui/test_entity_modals.py tests/ui/test_nest_preview.py tests/ui/test_hierarchy_table.py tests/ui/test_filter_panel.py tests/ui/test_task_board_view.py -v

# Linters
uv run ruff check src/docuflow/features/task_board/ src/docuflow/lib/widgets/ src/docuflow/features/chat/ src/docuflow/features/analytics/
uv run ruff format src/docuflow/features/task_board/ src/docuflow/lib/widgets/ src/docuflow/features/chat/ src/docuflow/features/analytics/
uv run pyright src/docuflow/features/task_board/ src/docuflow/lib/widgets/ src/docuflow/features/chat/ src/docuflow/features/analytics/

# Typecheck всего проекта
uv run pyright src

# Запуск приложения
uv run python -m docuflow.main
```

---

## Приоритеты выполнения

| Фаза | Приоритет | Причина |
|------|-----------|---------|
| 1 (ViewState) | 🔴 Высокий | Базовый UX, спека требует |
| 2 (FilterPanel) | 🔴 Высокий | Базовый функционал, спека требует |
| 7 (find_pallets_by_project) | 🟡 Средний | Метод простой, missing API |
| 4 (Part Library deeplink) | 🟡 Средний | Интеграция между модулями |
| 5 (Incidents) | 🟡 Средний | UX improvement |
| 6 (Chat channel) | 🟡 Средний | Низкая ценность, но спека требует |
| 8 (Analytics metric) | 🟡 Средний | Простое добавление |
| 9 (Complete dialog) | 🟢 Низкий | Улучшение UX, currently works without |
| 10 (Auto reservation) | 🟢 Низкий | Спека требует, но ручное резервирование есть |
| 11 (Create incident) | 🟢 Низкий | Дополнительная фича |

---

## Чек-лист коммитов

Каждая фаза — отдельный коммит:
```bash
git add -A
git commit -m "feat: ViewState persistence for hierarchy expansion (Task Board v2)"
git commit -m "feat: FilterPanel with presets (Task Board v2)"
git commit -m "feat: Part Library ↔ Task Board deeplink (Task Board v2)"
git commit -m "feat: Incident deeplink and project filters (Task Board v2)"
git commit -m "feat: Production channel in Chat (Task Board v2)"
git commit -m "feat: find_pallets_by_project API (Task Board v2)"
git commit -m "feat: pallet_by_project analytics metric (Task Board v2)"
git commit -m "feat: Complete task dialog with pallet selection (Task Board v2)"
git commit -m "feat: Auto material reservation on node assignment (Task Board v2)"
git commit -m "feat: Create incident button in TaskItemRow (Task Board v2)"
```
