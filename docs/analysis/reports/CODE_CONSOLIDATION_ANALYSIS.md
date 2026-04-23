# Анализ: Паттерны и возможности консолидации кодовой базы

> **Дата:** 2026-04-23  
> **Цель:** Выявить дублирование, общие паттерны и предложить хелперы/библиотеки для консолидации

---

## 1. Дублирование в View-слое (Наиболее болезненное)

### 1.1 Шаблон регистрации view
**Проблема:** Каждый `view.py` содержит одинаковый boilerplate:

```python
def register_xxx_view():
    ViewRegistry.register(
        ViewInfo(
            name="xxx",
            label="Xxx",
            icon="...",
            render_fn=xxx_view_wrapper,
            dependencies=[XxxSystem],
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )

async def xxx_view_wrapper(system: XxxSystem, system_scope: Any, layout: Any):
    view = XxxView(system, system_scope, layout)
    await view.render()

class XxxView(BaseDocuWidget):
    def __init__(self, system: XxxSystem, system_scope: Any, layout: Any):
        super().__init__(system_scope)
        self.system = system
        self.layout = layout
```

**Предложение:** Декоратор `@register_view` или метакласс:
```python
@register_view(name="warehouse", label="Warehouse", icon="inventory_2", system=InventorySystem)
class WarehouseView(BaseDocuWidget):
    ...
```

**Файлы:** `features/*/view.py` (15+ файлов)

### 1.2 Tailwind-классы inline
**Проблема:** 151+ использований inline Tailwind-классов в view.py:
```python
.classes("w-full h-full p-4 gap-4")
.classes("text-3xl font-bold text-white mb-2")
.classes("bg-white rounded-lg shadow-lg p-4")
```

**Предложение:** Константы/хелперы в `lib/widgets/styles.py`:
```python
CARD = "bg-white rounded-lg shadow-lg p-4"
PAGE_CONTAINER = "w-full h-full p-4 gap-4"
HEADING = "text-3xl font-bold text-white mb-2"
```

### 1.3 Диалоги подтверждения
**Проблема:** 29+ диалогов с одинаковой структурой (Cancel + OK/Confirm):
```python
with ui.dialog() as dialog:
    with ui.card():
        ui.label("...")
        with ui.row():
            ui.button("Cancel", on_click=dialog.close).props("flat text-color=slate-500")
            ui.button("OK", on_click=submit).props("unelevated color=primary")
```

**Предложение:** `lib/widgets/confirm_dialog.py`:
```python
async def confirm_dialog(title: str, message: str) -> bool:
    ...
```

### 1.4 Табы-навигация внутри view
**Проблема:** Повторяющийся паттерн `ui.tabs() + ui.tab_panels()` в:
- `inventory/view.py`
- `admin/view.py`
- `parts/view.py`
- `task_board/view.py`

**Предложение:** `lib/widgets/tabbed_view.py` — обёртка с декларативным API.

---

## 2. Дублирование в System-слое

### 2.1 SQL-шаблон: select + first()
**Проблема:** Более 50+ повторений:
```python
statement = select(X).where(X.y == z)
result = self.db_session.exec(statement).first()
```

**Предложение:** Методы в `BaseSystem`:
```python
class BaseSystem:
    def find_one(self, model, **filters) -> T | None:
        stmt = select(model)
        for k, v in filters.items():
            stmt = stmt.where(getattr(model, k) == v)
        return self.db_session.exec(stmt).first()
    
    def find_all(self, model, **filters) -> list[T]:
        ...
```

### 2.2 Commit + Refresh паттерн
**Проблема:** 21+ использований:
```python
self.db_session.add(obj)
self.db_session.commit()
self.db_session.refresh(obj)
```

**Предложение:** `BaseSystem.save(obj)`:
```python
def save(self, obj, refresh: bool = True):
    self.db_session.add(obj)
    self.db_session.commit()
    if refresh:
        self.db_session.refresh(obj)
    return obj
```

### 2.3 Импорты BaseSystem
**Проблема:** 15/15 system.py файлов импортируют `BaseSystem` из `application.base`.
**Статус:** Уже хорошо структурировано, но можно усилить `BaseSystem` общими методами.

---

## 3. Дублирование в Infrastructure

### 3.1 Ручное управление сессиями
**Проблема:** `AdminSystem` использует `with Session(self._engine)` вместо DI-сессии.
**Предложение:** Унифицировать через `BaseSystem` с fallback на engine.

### 3.2 Константы с дублированием
**Проблема:** Значения `coordinator_timeout` дублируются в `constants.py` и `test_config.py`.
**Статус:** Уже частично исправлено (тест обновлён).

---

## 4. Предложенные новые модули

### 4.1 `lib/widgets/styles.py` — Design System Tokens
```python
class Styles:
    CARD = "bg-white rounded-lg shadow-lg p-4"
    PAGE = "w-full h-full p-4 gap-4"
    HEADING = "text-2xl font-bold text-white"
    GRID = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
```

### 4.2 `lib/widgets/confirm_dialog.py` — Подтверждения
```python
async def confirm(title: str, msg: str, ok_text: str = "OK", ok_color: str = "primary") -> bool:
    ...

async def alert(title: str, msg: str, level: str = "info"):
    ...
```

### 4.3 `lib/widgets/data_table.py` — CRUD-таблицы
**Проблема:** Каждый view с таблицей повторяет код для:
- Колонок
- Кнопок Edit/Delete
- Пагинации
- Фильтров

```python
class CrudTable:
    def __init__(self, columns, on_edit, on_delete, ...):
        ...
```

### 4.4 `application/base.py` — Расширение BaseSystem
```python
class BaseSystem:
    def find_one(self, ...)
    def find_all(self, ...)
    def save(self, ...)
    def delete(self, ...)
```

---

## 5. Приоритет реализации

| Приоритет | Задача | Файлы | Эффект |
|-----------|--------|-------|--------|
| **High** | `BaseSystem` CRUD helpers | `application/base.py` | -50 SQL дублей |
| **High** | `@register_view` декоратор | `lib/widgets/view_registry.py` | -15 boilerplate |
| **Medium** | `styles.py` токены | `lib/widgets/styles.py` | -151 inline classes |
| **Medium** | `confirm_dialog` хелпер | `lib/widgets/confirm_dialog.py` | -29 диалогов |
| **Low** | `CrudTable` компонент | `lib/widgets/crud_table.py` | Унификация таблиц |

---

## 6. Метрики "до/после"

| Метрика | Текущее | После BaseSystem + register_view |
|---------|---------|----------------------------------|
| Строк `select().where()` | ~50+ | ~20 (сложные запросы) |
| Строк `db_session.commit()` | 21 | ~5 (в `save()`) |
| Inline `.classes(...)` | 151 | ~30 (специфичные) |
| `register_*_view` boilerplate | ~15×15 строк | 0 (декоратор) |
| Общий размер view.py | ~4000 строк | ~2800 строк (-30%) |
