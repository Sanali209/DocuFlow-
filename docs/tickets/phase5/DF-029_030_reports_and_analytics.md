# DF-029: reports/view.py

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 5 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-028](./DF-028_report_system.md) |

---

## Контекст

UI для выбора шаблона, ввода параметров и генерации PDF. Начальник нажимает 2 кнопки — получает готовый отчёт.

---

## Подзадачи

- [ ] **ReportsView** — главный экран:
  - Список шаблонов (карточки):
    - Название, описание, дата последнего использования
    - Кнопка "📄 Создать отчёт"

- [ ] **Генератор отчётов** (modal или отдельный экран):
  - Dynamically-rendered форма параметров из `ReportDataBlock.params`:
    - `date` → `ui.date()`
    - `str`  → `ui.input()`
    - `int`  → `ui.number()`
    - `node_id` → `ui.select(nodes)`
  - Кнопка "👁 Предпросмотр HTML" → открыть в вкладке (ui.open_tab())
  - Кнопка "📥 Скачать PDF" → вызвать system.generate() → ui.download()
  - Статус: "Генерируется..." spinner

- [ ] **Конструктор шаблонов** (для Начальника/Админа):
  - Список доступных блоков (из registry.available_blocks())
  - Drag & drop порядка блоков
  - Просмотр Jinja2 источника
  - Сохранить как новый шаблон / переименовать / удалить

- [ ] `lib/widgets/report_builder.py` — конструктор шаблонов

---

## Псевдокод

```python
class ReportsView:
    def render(self):
        with ui.column():
            ui.label("📄 Отчёты").classes("text-h5")
            
            templates = self.system.list_templates()
            with ui.grid(columns=3):
                for tmpl in templates:
                    with ui.card():
                        ui.label(tmpl.name).classes("text-bold")
                        if tmpl.description:
                            ui.label(tmpl.description).classes("text-caption")
                        if tmpl.last_used_at:
                            ui.label(f"Последний: {tmpl.last_used_at:%d.%m.%Y}")
                        ui.button("📄 Создать",
                                  on_click=lambda t=tmpl: self._open_generator(t))
    
    def _open_generator(self, template: ReportTemplate):
        # Собрать все уникальные params из всех блоков шаблона
        all_blocks = self.system.detect_blocks_in_template(template)
        all_params = {}
        for block in all_blocks:
            for param in block.params:
                all_params[param.name] = param
        
        with ui.dialog() as d, ui.card().classes("report-generator"):
            ui.label(f"Генерация: {template.name}").classes("text-h6")
            
            param_values = {}
            for param in all_params.values():
                if param.type == "date":
                    param_values[param.name] = ui.date(label=param.label)
                elif param.type == "node_id":
                    param_values[param.name] = ui.select(
                        self.sdk.coordination.get_nodes(), label=param.label)
                else:
                    param_values[param.name] = ui.input(label=param.label)
            
            spinner = ui.spinner(size="lg").set_visibility(False)
            
            async def generate_pdf():
                spinner.set_visibility(True)
                params = {k: v.value for k, v in param_values.items()}
                try:
                    pdf_bytes = self.system.generate(template, params)
                    ui.download(content=pdf_bytes,
                                filename=f"report_{datetime.now():%Y%m%d_%H%M}.pdf")
                except Exception as e:
                    ui.notify(f"Ошибка генерации: {e}", type="negative")
                finally:
                    spinner.set_visibility(False)
            
            ui.button("📥 Скачать PDF", on_click=generate_pdf).props("color=primary")
        d.open()
```

---

## TDD: Тесты

```python
async def test_reports_view_renders(mock_sdk):
    view = ReportsView(sdk=mock_sdk)
    await view.render()  # smoke test

async def test_generator_shows_params(mock_sdk, in_memory_db):
    """Динамическая форма параметров рендерится для шаблона."""
    template = ReportTemplate(
        name="Test",
        template_html="{{ blocks.work_items_summary(date_from=params.date_from) }}"
    )
    view = ReportsView(sdk=mock_sdk)
    # Должен правильно определить params из шаблона
    blocks = view.system.detect_blocks_in_template(template)
    assert any(b.name == "work_items_summary" for b in blocks)
```

---

## Definition of Done

```
✓ Список шаблонов рендерится в карточках
✓ Динамическая форма параметров (date/str/int) корректная для каждого шаблона
✓ "Скачать PDF" → файл скачивается в браузере
✓ Spinner показывается при генерации
✓ Ошибка → ui.notify() (не краш)
✓ Конструктор: добавление блоков + сохранение нового шаблона
```

---

# DF-030: analytics/view.py

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 5 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-028](./DF-028_report_system.md), [DF-013](../phase2/DF-013_task_board_system.md), [DF-024](../phase4/DF-023_024_chat_view_and_incidents.md) |
| **Gate** | **Gate 5** — финальный |

---

## Контекст

Управленческий дашборд для Начальника. Простые, понятные KPI без перегрузки. Упор на "что сейчас происходит" и "план vs факт". Данные из ReportSystem блоков.

---

## Подзадачи

- [ ] **AnalyticsView** — главный экран KPI:
  - Период: date picker (по умолчанию текущая смена/день)
  - Фильтр по узлу (select)

- [ ] **Карточки сводки** (верхняя строка):
  - Нарядов в работе: count(WorkItem IN_PROGRESS)
  - Завершено сегодня: count(WorkItem DONE where completed_at Today)
  - Листов порезано: sum(sheets_done) за период
  - Открытых инцидентов: count(IncidentLog resolved=False)

- [ ] **График: план vs факт** (по узлам):
  - X: название узла
  - Y: estimated_minutes (синий) vs actual_minutes (красный)
  - Подпись: drift% для каждого узла

- [ ] **Таблица: незакрытые наряды**:
  - Колонки: folder_name, статус badge, дней в работе, причина задержки
  - Сортировка: дней в работе DESC

- [ ] **Простои**: summary карточка общего времени по типам инцидентов за период

- [ ] **Загрузка узлов**: таблица по лазерам:
  - task_count, sheets_done, % от плана, статус (активен/простой)

> ⚠️ **Принцип**: не перегружать. Максимум 5-6 элементов на экране. Если нужно больше деталей — использовать Reports (DF-029).

---

## Псевдокод

```python
class AnalyticsView:
    def render(self):
        with ui.column().classes("analytics-dashboard"):
            # Фильтры периода
            with ui.row():
                date_from = ui.date(label="С")
                date_to   = ui.date(label="По")
                node_sel  = ui.select(["Все"] + self._nodes(), label="Узел")
                ui.button("Обновить", on_click=self._refresh)
            
            # Сводка KPI (карточки)
            with ui.row().classes("kpi-row"):
                self._kpi_card("📋 В работе",
                    self.system.count_work_items(status=IN_PROGRESS))
                self._kpi_card("✅ Готово сегодня",
                    self.system.count_work_items(status=DONE, date=today()))
                self._kpi_card("📊 Листов порезано",
                    self.system.sum_sheets_done(date_from.value, date_to.value))
                self._kpi_card("⚡ Открытых инцидентов",
                    self.incident_system.count_open())
            
            # График план vs факт
            ui.label("📈 Время: план vs факт по узлам").classes("text-h6")
            tasks_data = self.system.get_blocks("estimated_vs_actual", {
                "date_from": date_from.value,
                "date_to":   date_to.value
            })
            self._render_drift_chart(tasks_data)
            
            # Незакрытые наряды
            ui.label("⚠️ Незакрытые наряды").classes("text-h6")
            overdue = [wi for wi in self.system.list(filters={"status": [IN_PROGRESS, ON_HOLD, BLOCKED]})
                       if wi.days_open > 3]
            ui.table(rows=[{
                "folder": wi.folder_name,
                "status": wi.status.value,
                "days":   wi.days_open,
                "reason": wi.block_reason or "—"
            } for wi in overdue])
    
    def _kpi_card(self, label: str, value):
        with ui.card().classes("kpi-card"):
            ui.label(str(value)).classes("text-h4 text-bold")
            ui.label(label).classes("text-caption")
```

---

## TDD: Тесты

```python
async def test_analytics_view_renders(mock_sdk):
    view = AnalyticsView(sdk=mock_sdk)
    await view.render()  # smoke test

def test_kpi_card_count_in_progress(in_memory_db):
    # Создать 3 WorkItem в IN_PROGRESS, 2 в DONE
    wi_system = WorkItemSystem(session=in_memory_db)
    # ...
    count = wi_system.count_work_items(status=WorkItemStatus.IN_PROGRESS)
    assert count == 3

def test_sum_sheets_done(in_memory_db):
    # Создать TaskItem с sheets_done=5 и sheets_done=3
    system = TaskBoardSystem(session=in_memory_db)
    # ...
    total = system.sum_sheets_done(date_today, date_today)
    assert total == 8
```

---

## Definition of Done (Gate 5 ✅ — ФИНАЛЬНЫЙ)

```
Gate 5 PASSED если:
  ✓ DF-028: ReportSystem.generate() → PDF байты
  ✓ DF-029: reports/view.py: 2 клика → PDF скачан
  ✓ DF-030: analytics/view.py: KPI карточки с реальными данными
  ✓ analytics: drift% по узлам отображается
  ✓ analytics: незакрытые наряды видны
  ✓ Все unit тесты проходят (pytest tests/)
  ✓ END-TO-END ТЕСТ:
      1. FolderScanner обнаруживает папку с GNC
      2. Бригадир создаёт батч + регистрирует документ
      3. Оператор берёт батч → обновляет листы → завершает
      4. Создаётся ProductionUnit с label_id
      5. Начальник генерирует отчёт за смену → PDF
      6. Analytics показывает правильный drift%
  ✓ Нет незакрытых критических багов
  ✓ Все 5 Gates пройдены
```
