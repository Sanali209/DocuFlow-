# DF-028: ReportSystem (Registry + PDF)

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 5 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md), все системы (данные для блоков) |
| **Блокирует** | [DF-029](./DF-029_reports_view.md), [DF-030](./DF-030_analytics_view.md) |
| **Архитектура** | [02_application_architecture.md §4.7](../architecture/02_application_architecture.md) |
| **Data Flow** | [03_data_flow.md §10](../architecture/03_data_flow.md) |

---

## Контекст

Модульная система отчётов. Каждый феатур-модуль регистрирует свои блоки данных при on_startup. Шаблоны (Jinja2 HTML) хранятся в БД. Рендер → PDF через weasyprint.

---

## Execution Plan

```
1. Реализовать ReportDataBlock + ReportRegistry
2. Зарегистрировать блоки из всех модулей (on_startup)
3. Реализовать ReportSystem.generate()
4. Написать встроенные HTML шаблоны
5. Протестировать PDF генерацию на реальных данных
```

---

## Подзадачи

### Registry
- [ ] `ReportDataBlock`:
  ```python
  @dataclass
  class ReportDataBlock:
      name: str            # "work_items_summary"
      label: str           # "Сводка нарядов"
      params: list[BlockParam]  # описание параметров блока
      query_fn: Callable   # (session, params) → list[dict]
  ```
- [ ] `ReportRegistry`:
  - `register(block: ReportDataBlock)`
  - `get_block(name: str) -> ReportDataBlock`
  - `available_blocks() -> list[ReportDataBlock]`
  - `BlockProxy` — объект для Jinja2: `{{ blocks.work_items_summary(date_from=...) }}`

### Блоки данных (регистрируются в on_startup каждого System)
- [ ] **WorkItemSystem** регистрирует:
  - `"work_items_summary"` → list[{folder_name, status, type, task_count, ...}]
  - `"work_item_detail"` → полная карточка наряда
- [ ] **TaskBoardSystem** регистрирует:
  - `"tasks_by_node"` → пары [node_id, task_count, sheets_done, estimated_min]
  - `"shift_completion"` → % выполненных задач за смену
  - `"estimated_vs_actual"` → [{task, estimated, actual, drift_pct}]
- [ ] **MaterialSystem** регистрирует:
  - `"material_usage"` → движения материала за период
  - `"stock_snapshot"` → остатки на дату
- [ ] **IncidentSystem** регистрирует:
  - `"incident_log"` → list всех инцидентов за период
  - `"downtime_summary"` → {incident_type: total_minutes}
- [ ] **PartLibrarySystem** регистрирует:
  - `"parts_produced"` → {sku: qty_produced} за период

### ReportSystem
- [ ] `generate(template: ReportTemplate, params: dict) -> bytes`:
  - Создать BlockProxy с registry + params
  - `context = {"blocks": proxy, "params": params, "now": datetime.now()}`
  - `html = jinja2_env.render(template.template_html, context)`
  - `pdf = HTML(string=html).write_pdf()`
  - return pdf bytes

### Встроенные шаблоны (seed в БД при первом запуске)
- [ ] `"shift_report"` — отчёт по смене:
  - Разделы: задачи по узлам, листов порезано, drift%, инциденты за смену
- [ ] `"work_item_report"` — ход наряда:
  - Задачи + статусы + MaterialAudit + ProductionUnit
- [ ] `"material_report"` — движение материала за период
- [ ] `"incident_report"` — лог инцидентов + простои

---

## Псевдокод

```python
class BlockProxy:
    """
    Прокси для Jinja2 шаблонов.
    Позволяет вызывать блоки как функции в шаблоне:
      {{ blocks.work_items_summary(date_from=params.date_from) }}
    """
    def __init__(self, registry: ReportRegistry, session, global_params: dict):
        self._registry = registry
        self._session  = session
        self._params   = global_params
    
    def __getattr__(self, name: str):
        block = self._registry.get_block(name)
        if not block:
            raise AttributeError(f"Unknown report block: {name}")
        def call(**kwargs):
            merged_params = {**self._params, **kwargs}
            return block.query_fn(self._session, merged_params)
        return call


class ReportSystem(BaseSystem):
    
    def generate(self, template: ReportTemplate, params: dict) -> bytes:
        """
        Рендерит HTML шаблон через Jinja2 + конвертирует в PDF.
        
        Raises: jinja2.TemplateError если шаблон сломан
                ImportError если weasyprint не установлен
        """
        proxy = BlockProxy(self.registry, self.session, params)
        context = {
            "blocks": proxy,
            "params": params,
            "now":    datetime.now(),
        }
        jinja_env = Environment(loader=BaseLoader())
        html_str  = jinja_env.from_string(template.template_html).render(**context)
        
        # PDF generation
        from weasyprint import HTML
        return HTML(string=html_str).write_pdf()
    
    async def on_startup(self) -> None:
        """Регистрирует собственные блоки при старте."""
        # Каждый другой System также регистрирует свои блоки
        # через sdk.report_registry.register(...)
        await self._seed_default_templates()


# Пример регистрации блока (в WorkItemSystem.on_startup):
def _register_report_blocks(self) -> None:
    self.sdk.report_registry.register(ReportDataBlock(
        name="work_items_summary",
        label="Сводка нарядов",
        params=[
            BlockParam("date_from", "Дата с", "date"),
            BlockParam("date_to",   "Дата по", "date"),
        ],
        query_fn=self._query_work_items_summary
    ))

def _query_work_items_summary(self, session, params: dict) -> list[dict]:
    date_from = params.get("date_from")
    date_to   = params.get("date_to")
    query = select(WorkItem)
    if date_from: query = query.where(WorkItem.created_at >= date_from)
    if date_to:   query = query.where(WorkItem.created_at <= date_to)
    items = session.exec(query).all()
    return [
        {"folder_name": wi.folder_name,
         "status":      wi.status.value,
         "type":        wi.work_item_type.value,
         "task_count":  len(wi.task_items)}
        for wi in items
    ]
```

### Пример Jinja2 шаблона

```html
<!-- shift_report template (хранится в ReportTemplate.template_html) -->
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #ddd; padding: 8px; }
    th { background: #f0f0f0; }
    .red { color: #cc0000; }
  </style>
</head>
<body>
  <h1>Отчёт по смене</h1>
  <p>Дата: {{ params.date_from }} — {{ params.date_to }}</p>
  <p>Сгенерирован: {{ now.strftime('%d.%m.%Y %H:%M') }}</p>

  <h2>Задачи по узлам</h2>
  <table>
    <tr><th>Узел</th><th>Задач</th><th>Листов</th><th>Drift%</th></tr>
    {% for row in blocks.tasks_by_node(date_from=params.date_from, date_to=params.date_to) %}
    <tr>
      <td>{{ row.node_id }}</td>
      <td>{{ row.task_count }}</td>
      <td>{{ row.sheets_done }}</td>
      <td class="{{ 'red' if row.drift_pct > 20 else '' }}">{{ row.drift_pct }}%</td>
    </tr>
    {% endfor %}
  </table>

  <h2>Инциденты</h2>
  {% for inc in blocks.incident_log(date_from=params.date_from, date_to=params.date_to) %}
  <p>⚡ {{ inc.incident_type }}: {{ inc.description }} ({{ inc.reported_by }})</p>
  {% endfor %}
</body>
</html>
```

---

## TDD: Тесты

```python
def test_registry_register_and_get():
    registry = ReportRegistry()
    block = ReportDataBlock(name="test_block", label="Test",
                            params=[], query_fn=lambda s, p: [{"x": 1}])
    registry.register(block)
    assert registry.get_block("test_block") is block

def test_block_proxy_calls_query(in_memory_db):
    registry = ReportRegistry()
    registry.register(ReportDataBlock(
        name="my_block", label="My", params=[],
        query_fn=lambda session, params: [{"result": params.get("x")}]
    ))
    proxy = BlockProxy(registry, in_memory_db, {"x": 42})
    result = proxy.my_block()  # через __getattr__
    assert result == [{"result": 42}]

def test_generate_html_renders(in_memory_db):
    system = ReportSystem(session=in_memory_db, registry=ReportRegistry())
    template = ReportTemplate(
        name="test",
        template_html="<h1>{{ params.title }}</h1>"
    )
    pdf = system.generate(template, {"title": "Test Report"})
    assert isinstance(pdf, bytes)
    assert len(pdf) > 0

def test_unknown_block_raises():
    proxy = BlockProxy(ReportRegistry(), None, {})
    with pytest.raises(AttributeError, match="Unknown report block"):
        _ = proxy.nonexistent_block
```

---

## Definition of Done

```
✓ ReportRegistry: register / get_block / available_blocks работают
✓ BlockProxy: вызов блока как атрибута через __getattr__
✓ generate() → bytes (PDF) на шаблоне с {{ blocks.xxx() }}
✓ Четыре встроенных шаблона посеяны при первом запуске
✓ Каждый System регистрирует свои блоки при on_startup
✓ Неизвестный блок → AttributeError (не silent fail)
✓ Все тесты проходят (включая реальную PDF генерацию)
```
