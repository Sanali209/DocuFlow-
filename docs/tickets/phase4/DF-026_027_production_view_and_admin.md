# DF-026: production/view.py

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 4 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-025](./DF-025_production_system.md) |

---

## Контекст

Склад готовых деталей. Кладовщик ищет паллеты по label_id и управляет их размещением. Поиск по части label_id (live) — ключевая фича, потому что нет QR-сканера.

---

## Подзадачи

- [ ] **ProductionView** — главный экран склада:
  - Поисковое поле с live search по label_id (partial):
    - Ввод "07-А" → немедленно показывает "25-07-А-001", "25-07-А-002"...
    - Минимум 2 символа для запуска поиска
  - Таблица результатов:
    - label_id, qty_produced, материал, место (StorageLocation), дата создания, is_stock бейдж
  - Фильтры: is_stock / is_pre_system / StorageLocation / дата

- [ ] **Карточка ProductionUnit** (modal):
  - label_id (крупный, copyable)
  - TaskItem info + WorkItem ссылка
  - Список деталей (из TaskPart): SKU, qty, SVG превью
  - StorageLocation: читаемое название + кнопка "Обновить место"
  - Кнопки:
    - "✂️ Разделить" → диалог qty_to_stock
    - "🔗 Объединить" → выбрать другие паллеты
    - "📦 В запас" → unit.is_stock = True
    - "📂 Открыть папку" → explorer.exe

- [ ] **Создание паллеты** (из TaskBoard при завершении задачи — DF-013):
  - Диалог "Куда кладём?":
    - Поле "Код места" (autocomplete StorageLocation)
    - Поле "Кол-во деталей" (default = qty_produced)
    - Кнопка "К существующей паллете" → live search по label_id
    - Кнопка "Новая паллета" → создать + показать ярлык

- [ ] **Обратный поиск** (из PartLibrary):
  - Поиск по SKU → список всех паллет с этой деталью

---

## Псевдокод

```python
class ProductionView:
    def render(self):
        with ui.column().classes("full-width"):
            # Live search
            search = ui.input("Поиск: label_id или SKU",
                              on_change=lambda: self._on_search_change(search.value))
            
            with ui.row():
                ui.checkbox("Только запас", on_change=lambda v: self._apply_filter())
                ui.select(self._locations, label="Место", on_change=...)
            
            self.results_table = ui.table(rows=[], columns=COLUMNS)
            self.results_table.on_row_click(lambda r: self._show_unit_card(r))
    
    def _on_search_change(self, query: str):
        if len(query) < 2:
            return
        # Debounce 300ms (NiceGUI timer trick)
        results = self.system.search_units(query)
        self.results_table.rows = [unit_to_row(r) for r in results]
        self.results_table.update()
    
    def _show_unit_card(self, unit: ProductionUnit):
        with ui.dialog() as d, ui.card().classes("unit-card"):
            ui.label(unit.label_id).classes("text-h4 text-bold copyable")
            
            if unit.task_item:
                ui.label(f"Наряд: {unit.task_item.work_item.folder_name}")
                for part in unit.task_item.task_parts:
                    with ui.row():
                        PartPreviewWidget(svg_path=part.part_library.svg_preview_path)
                        ui.label(f"{part.part_sku} × {part.qty}")
            
            loc_input = ui.input(
                "Место хранения",
                value=unit.storage_location.code if unit.storage_location else ""
            )
            ui.button("💾 Сохранить место",
                      on_click=lambda: self.system.update_location(
                          unit.label_id, loc_input.value))
            
            with ui.row():
                ui.button("✂️ Разделить", on_click=lambda: self._split_dialog(unit))
                ui.button("📦 В запас", on_click=lambda: [
                    setattr(unit, "is_stock", True),
                    self.system.session.commit()
                ])
        d.open()
```

---

## TDD: Тесты

```python
async def test_production_view_renders(mock_sdk):
    view = ProductionView(sdk=mock_sdk)
    await view.render()  # smoke test

async def test_search_fires_on_2_chars(mock_sdk, in_memory_db):
    system = ProductionSystem(session=in_memory_db)
    system.create_unit(task_item_id=1, qty_produced=10, node_code="А")
    
    view = ProductionView(system=system)
    await view._on_search_change("07")  # должен найти
    assert len(view.results_table.rows) >= 1

async def test_search_skips_1_char(mock_sdk):
    view = ProductionView(...)
    await view._on_search_change("0")  # меньше 2 символов
    assert view.results_table.rows == []  # не запускать поиск
```

---

## Definition of Done (Gate 4 — частично)

```
✓ Live search по partial label_id работает (минимум 2 символа)
✓ Карточка паллеты: детали с SVG превью
✓ "Обновить место" сохраняет StorageLocation
✓ "Разделить" вызывает ProductionSystem.split() + обновляет таблицу
✓ "В запас" меняет is_stock = True
✓ Обратный поиск по SKU работает через PartLibraryView
```

---

# DF-027: Admin Panel улучшения

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 4 |
| **Priority** | 🟢 MEDIUM |
| **Зависит от** | [DF-015](../phase2/DF-014_015_016_views_presets_widgets.md), [DF-008](../phase1/DF-008_009_notifications_and_view.md) |
| **Gate** | Gate 4 |

---

## Контекст

Admin = разработчик/поддержка. Admin Panel расширяется для управления всеми глобальными настройками: NotificationTemplate, ViewPreset, роли/пользователи, мониторинг кластера.

---

## Подзадачи

- [ ] **NotificationTemplate редактор**:
  - Таблица шаблонов: key, текст, enabled toggle
  - Inline редактирование текста (Jinja2)
  - Кнопка "Тест рендера" → диалог с вводом переменных → показать результат
  - Reset to defaults кнопка

- [ ] **ViewPreset менеджер**:
  - CRUD для global-пресетов (owner="global")
  - Список по модулям (work_items / task_board / ...)
  - Импорт/экспорт preset_json

- [ ] **User/Role Matrix редактор**:
  - Таблица: пользователи × разрешения
  - Toggle для каждого разрешения
  - Назначить Workplace пользователю

- [ ] **Cluster Monitor** (уже частично есть):
  - Список узлов: node_id, last_heartbeat, is_master, last_snapshot
  - Trigger manual snapshot sync
  - Force re-election мастера

- [ ] **MaterialType Manager**:
  - Глобальный список типов материалов
  - Редактирование time params (cut_speed, pierce_time, idle_speed, tolerance%)

---

## Definition of Done (Gate 4 ✅)

```
Gate 4 PASSED если (DF-022..DF-027):
  ✓ Чат: send/reply/thread/attach работают
  ✓ Инциденты: report → чат + resolve → downtime
  ✓ ProductionUnit: create → split → search by partial label_id
  ✓ production/view.py: live search 2+ символа
  ✓ Admin: NotificationTemplate редактируется через UI
  ✓ Admin: ViewPreset global пресеты CRUD
  ✓ Все unit тесты проходят (pytest tests/unit/phase4/)
```
