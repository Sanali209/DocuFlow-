# DF-014: task_board/view.py

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 2 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-013](./DF-013_task_board_system.md), [DF-015](./DF-015_view_preset.md), [DF-016](./DF-016_core_widgets.md) |
| **Gate** | Gate 2 (частично) |

---

## Контекст

Два основных вида:
1. **Вид Оператора** — корзина, батчи, прогресс листов, статусы
2. **Вид Бригадира** — все активные узлы, батчинг инструменты, приоритеты

Самый используемый экран в системе — качество UI критично.

---

## Подзадачи

### Вид Оператора
- [ ] 📥 Корзина (WorkerBucket):
  - Карточки батчей (BatchCard): материал, листов, estimated_minutes, drift%
  - Внутри батча: список TaskItem с прогресс-баром `sheets_done/sheet_qty`
  - Кнопки: "▶ Начать" / "⏸ Пауза" / "✅ Завершить" / "🔒 Заблокировать"
  - "Завершить" → диалог: sheets_done input + "Куда кладём?" (создание ProductionUnit, DF-025)
- [ ] 📊 Прогресс текущей задачи: живой таймер (elapsed) vs estimated
- [ ] 🔔 Алерт NS Mirror если файл устарел
- [ ] ⏱ Ввод причины паузы (on_hold dialog)

### Вид Бригадира
- [ ] Все узлы — панели (по одной на каждый лазер):
  - Что сейчас режет, прогресс, статус
  - Drift% с цветовой кодировкой (green/yellow/red)
- [ ] Инструменты батчинга:
  - Кнопка "Авто-батчинг" → BatchEngine.compute() → предложить группировку
  - Drag & Drop задач между батчами
  - "Создать батч вручную" / "Разбить батч"
  - STOCK_ALERT баннер (если деталь есть в запасе)
- [ ] Приоритет: input number per TaskItem
- [ ] "Заблокировать": диалог с причиной → TaskItem(BLOCKED)
- [ ] Фильтр: по узлу, по материалу, по статусу

### Передача смены
- [ ] Кнопка "Передать смену" (в виде оператора):
  - Диалог: handover_note textarea
  - Кнопка подтверждения → ChatMessage(HANDOVER)

### Виджеты
- [ ] `lib/widgets/batch_card.py` — карточка батча
- [ ] `lib/widgets/task_item_row.py` — строка таска с прогресс-баром
- [ ] `lib/widgets/bucket_panel.py` — корзина оператора целиком
- [ ] `lib/widgets/explorer_button.py` — кнопка "📂 Открыть папку"

---

## Псевдокод

```python
# Вид Оператора: bucket_panel отображение

class OperatorBucketView:
    def render(self):
        with ui.column():
            ui.label(f"Вы: {self.user} @ {self.node_id}").classes("text-h6")
            
            for batch in self.system.get_bucket(self.node_id):
                with ui.card().classes("batch-card"):
                    ui.label(f"📦 {batch.mat_type} | {batch.total_sheets} листов")
                    ui.label(f"⏱ {batch.estimated_minutes} мин "
                             f"| Drift: {self.system.get_drift(batch):.1f}%")
                    
                    for task in batch.tasks:
                        with ui.row():
                            StatusBadge(task.status).render()
                            ui.label(task.file_name)
                            ui.linear_progress(
                                value=task.sheets_done / (task.sheet_qty or 1)
                            ).props("stripe color=green")
                            ui.label(f"{task.sheets_done}/{task.sheet_qty}")
                            
                            if task.status == TaskItemStatus.PLANNED:
                                ui.button("▶ Начать", 
                                    on_click=lambda t=task: self.system.start_task(t.id))
                            elif task.status == TaskItemStatus.IN_PROGRESS:
                                ui.button("⏸ Пауза",
                                    on_click=lambda t=task: self._pause_dialog(t))
                                ui.button("✅ Завершить",
                                    on_click=lambda t=task: self._complete_dialog(t))

    def _complete_dialog(self, task: TaskItem):
        with ui.dialog() as d, ui.card():
            sheets = ui.number("Листов порезано", value=task.sheet_qty)
            ui.button("ОК", on_click=lambda: [
                self.system.complete_task(task.id, int(sheets.value), ...),
                self._show_production_unit_dialog(task),
                d.close()
            ])
        d.open()
```

---

## TDD: Тесты

```python
async def test_operator_view_renders(mock_sdk):
    view = OperatorBucketView(sdk=mock_sdk, node_id="LASER_1")
    await view.render()  # smoke test

def test_batch_card_shows_drift(mock_batch):
    mock_batch.estimated_minutes = 60
    mock_batch.actual_minutes = 90
    card = BatchCard(mock_batch)
    assert "50" in card.drift_label  # 50% drift
```

---

## Definition of Done (Gate 2 ✅)

```
Gate 2 PASSED если (это + DF-010..DF-016):
  ✓ Оператор может: взять батч → начать → добавить листы → завершить
  ✓ Бригадир видит: все узлы + батчи + drift%
  ✓ Авто-батчинг предлагает группировку правильно
  ✓ Drag & Drop задач между батчами работает
  ✓ Handover: смена передаётся с заметкой в чат
  ✓ STOCK_ALERT отображается при наличии деталей в запасе
  ✓ "📂 Открыть в Explorer" работает
  ✓ ViewPreset вкладки переключаются
```

---

# DF-015: ViewPreset система

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 2 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md) |
| **Блокирует** | [DF-011](./DF-011_012_work_items_view_and_batch_engine.md), [DF-014](./DF-014_task_board_view.md) |

---

## Контекст

Notion-подобные пресеты видов. Каждый модуль может иметь несколько именованных пресетов (table/kanban/list/cards) с разными фильтрами и группировкой. Пресеты бывают личные (owner=username) и общие (owner="global").

---

## Подзадачи

- [ ] `ViewPreset` сущность уже в DF-001
- [ ] `ViewPresetSystem`:
  - `create(module, owner, name, preset_json)` → ViewPreset
  - `list(module, owner) -> list[ViewPreset]`
  - `get_active(module, owner) -> ViewPreset`
  - `set_active(module, owner, preset_id)`
  - `delete(preset_id, owner)` — нельзя удалять "global" без прав
- [ ] `preset_json` schema:
  ```json
  {
    "view_type": "table|kanban|list|cards",
    "columns": ["col1", "col2"],
    "filters": {"status": ["NEW", "REGISTERED"]},
    "sort": {"field": "created_at", "dir": "desc"},
    "group_by": "project_id"
  }
  ```
- [ ] `lib/widgets/view_preset_switcher.py`:
  - Вкладки с именами пресетов (Notion-style)
  - Кнопка "+" → создать пресет
  - Правый клик → переименовать / удалить
  - При переключении → emit(preset_changed, preset)

---

## TDD: Тесты

```python
def test_list_presets_personal_and_global():
    system = ViewPresetSystem(...)
    system.create("work_items", "global", "Все активные", {...})
    system.create("work_items", "user1",  "Мои задачи",   {...})
    
    presets = system.list("work_items", "user1")
    assert len(presets) == 2  # видит и global и своё

def test_delete_global_preset_without_permission():
    preset = ViewPreset(owner="global", ...)
    with pytest.raises(PermissionError):
        system.delete(preset.id, owner="regular_user")
```

---

## Definition of Done

```
✓ Личные и глобальные пресеты хранятся раздельно
✓ list() возвращает и global и personal пресеты
✓ Виджет-переключатель устанавливает активный пресет
✓ preset_json применяется как фильтр/сортировка в таблице
✓ Обычный пользователь не может удалить "global" пресет
```

---

# DF-016: Core UI виджеты

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 2 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md) |

---

## Подзадачи (все виджеты в `lib/widgets/`)

- [ ] `status_badge.py` — цветные статус бейджи (WorkItem + TaskItem)
- [ ] `work_item_card.py` — компонент карточки наряда (используется в нескольких views)
- [ ] `task_item_row.py` — строка задачи с прогресс-баром
- [ ] `material_chip.py` — чипс "AA 5052-H32 / 3mm / green"
- [ ] `part_preview.py` — SVG превью детали (из PartLibrary)
- [ ] `scan_log_panel.py` — live лог сканера (WorkLog scroll)
- [ ] `file_changed_alert.py` — баннер "Файл изменился на сети"
- [ ] `explorer_button.py` — кнопка "📂 Открыть в Explorer"
- [ ] `ns_mirror_status.py` — индикатор NS Mirror синхронизации

---

## Definition of Done

```
✓ Каждый виджет: изолированный компонент с чёткими props
✓ Smoke тесты: каждый виджет рендерится без ошибок
✓ StatusBadge: правильные цвета для всех статусов
✓ explorer_button: вызывает subprocess.Popen(["explorer.exe", path])
```
