# DF-019: PartLibrarySystem (поиск + SVG)

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 3 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md), [DF-005](../phase1/DF-005_svg_generator.md), [DF-006](../phase1/DF-006_folder_scanner_system.md) |
| **Блокирует** | [DF-020](./DF-020_part_library_view.md) |
| **Data Flow** | [03_data_flow.md §2](../architecture/03_data_flow.md) |

---

## Контекст

PartLibrary — справочник всех деталей, которые система когда-либо видела. Пополняется автоматически при сканировании GNC. Содержит реальный bbox из SVGGenerator. Умный поиск нужен кладовщику для нахождения аналогичных деталей.

---

## Execution Plan

```
1. Написать тесты для find_by_bbox()
2. Реализовать PartLibrarySystem с CRUD
3. Реализовать search() с множеством критериев
4. Реализовать inverse_search() — деталь → наряды → паллеты
5. Реализовать PartTemplate CRUD
```

---

## Подзадачи

### CRUD
- [ ] `upsert_part(sku, mat_type_id?, bbox_x?, bbox_y?, contour_count, hole_count, corner_count, svg_path?) -> PartLibrary`:
  - Ключ: `sku` (уникальный)
  - При существующей: обновить bbox и метрики если есть новые данные
  - `first_seen_at` — не перезаписывать
  - `last_seen_at = now()`
- [ ] `get_part(sku) -> Optional[PartLibrary]`

### Поиск
- [ ] `search(query?) -> list[PartLibrary]`:
  - По `sku` (partial, case-insensitive)
  - По `name` (partial)
  - По `mat_type_id`
- [ ] `find_by_bbox(bbox_x, bbox_y, tolerance_pct=5.0) -> list[PartLibrary]`:
  - WHERE `bbox_x` BETWEEN `bbox_x * (1 - tol/100)` AND `bbox_x * (1 + tol/100)`
  - AND `bbox_y` BETWEEN `bbox_y * (1 - tol/100)` AND `bbox_y * (1 + tol/100)`
- [ ] `find_by_metrics(contour_count?, hole_count?, corner_count?) -> list[PartLibrary]`

### Обратный поиск
- [ ] `get_work_items_for_part(sku) -> list[WorkItem]`:
  - TaskPart → TaskItem → WorkItem WHERE part_sku == sku
- [ ] `get_production_units_for_part(sku) -> list[ProductionUnit]`:
  - TaskPart → TaskItem → ProductionUnit WHERE part_sku == sku

### PartTemplate
- [ ] `create_template(sku, message, severity, author) -> PartTemplate`
- [ ] `get_templates(sku) -> list[PartTemplate]`
- [ ] `delete_template(template_id)`

---

## Псевдокод

```python
class PartLibrarySystem(BaseSystem):
    
    def upsert_part(self, sku: str, **kwargs) -> PartLibrary:
        """
        Идемпотентное создание/обновление детали.
        Вызывается из FolderScanner при каждом парсинге GNC.
        first_seen_at сохраняется при первом создании.
        """
        part = self.session.get(PartLibrary, sku)
        if part:
            # Обновляем только если новые данные лучше (не None)
            for field, value in kwargs.items():
                if value is not None:
                    setattr(part, field, value)
            part.last_seen_at = datetime.now()
        else:
            part = PartLibrary(sku=sku, first_seen_at=datetime.now(),
                               last_seen_at=datetime.now(), **kwargs)
            self.session.add(part)
        self.session.commit()
        return part
    
    def find_by_bbox(self, bbox_x: float, bbox_y: float,
                     tolerance_pct: float = 5.0) -> list[PartLibrary]:
        """
        Поиск деталей по размерам с допуском.
        Необходим для поиска "похожих" деталей при нехватке ресурсов.
        """
        tol = tolerance_pct / 100.0
        return self.session.exec(
            select(PartLibrary)
            .where(PartLibrary.bbox_x.between(
                bbox_x * (1 - tol), bbox_x * (1 + tol)))
            .where(PartLibrary.bbox_y.between(
                bbox_y * (1 - tol), bbox_y * (1 + tol)))
        ).all()
    
    def get_production_units_for_part(self, sku: str) -> list:
        """
        Обратный поиск: SKU → все паллеты где есть эта деталь.
        Используется для поиска готовых деталей на складе.
        """
        return self.session.exec(
            select(ProductionUnit)
            .join(TaskItem, ProductionUnit.task_item_id == TaskItem.id)
            .join(TaskPart, TaskPart.task_item_id == TaskItem.id)
            .where(TaskPart.part_sku == sku)
        ).all()
```

---

## TDD: Тесты

```python
def test_upsert_part_creates_new(in_memory_db):
    system = PartLibrarySystem(session=in_memory_db)
    part = system.upsert_part("3433-11-004-G", bbox_x=250.0, bbox_y=80.0,
                               contour_count=5, hole_count=2, corner_count=12)
    assert part.sku == "3433-11-004-G"
    assert part.bbox_x == 250.0
    assert part.first_seen_at is not None

def test_upsert_part_does_not_overwrite_first_seen(in_memory_db):
    system = PartLibrarySystem(session=in_memory_db)
    first_call  = system.upsert_part("SKU-A", bbox_x=100.0, ...)
    second_call = system.upsert_part("SKU-A", bbox_x=110.0, ...)
    assert second_call.first_seen_at == first_call.first_seen_at  # не изменилось

def test_find_by_bbox_with_tolerance():
    system = PartLibrarySystem(session=in_memory_db)
    system.upsert_part("PART-A", bbox_x=200.0, bbox_y=100.0, ...)
    system.upsert_part("PART-B", bbox_x=500.0, bbox_y=200.0, ...)
    
    results = system.find_by_bbox(200.0, 100.0, tolerance_pct=5.0)
    assert len(results) == 1
    assert results[0].sku == "PART-A"

def test_find_by_bbox_no_results():
    system = PartLibrarySystem(session=in_memory_db)
    system.upsert_part("PART-A", bbox_x=200.0, bbox_y=100.0, ...)
    
    results = system.find_by_bbox(500.0, 500.0, tolerance_pct=5.0)
    assert len(results) == 0

def test_get_work_items_for_part(in_memory_db):
    """Обратный поиск: SKU → WorkItem-ы."""
    wi   = WorkItem(folder_name="SIDRA-001", ...)
    task = TaskItem(work_item_id=wi.id, ...)
    tp   = TaskPart(task_item_id=task.id, part_sku="TEST-SKU", ...)
    # ... add to db
    
    system = PartLibrarySystem(session=in_memory_db)
    work_items = system.get_work_items_for_part("TEST-SKU")
    assert len(work_items) == 1
    assert work_items[0].folder_name == "SIDRA-001"

def test_part_template_crud(in_memory_db):
    system = PartLibrarySystem(session=in_memory_db)
    tmpl = system.create_template(
        sku="TEST-SKU",
        message="Эта деталь разрушает сопла",
        severity="warning",
        author="foreman1"
    )
    templates = system.get_templates("TEST-SKU")
    assert len(templates) == 1
    assert templates[0].severity == "warning"

def test_delete_template(in_memory_db):
    system = PartLibrarySystem(session=in_memory_db)
    tmpl = system.create_template("SKU", "msg", "info", "user")
    system.delete_template(tmpl.id)
    assert system.get_templates("SKU") == []
```

---

## Definition of Done

```
✓ upsert_part() идемпотентен — повторный вызов не создаёт дубль
✓ first_seen_at никогда не перезаписывается
✓ find_by_bbox() с tolerance_pct=5% находит детали в диапазоне
✓ get_work_items_for_part() корректный обратный поиск
✓ get_production_units_for_part() — деталь → паллеты
✓ PartTemplate: create / get / delete работают
✓ Все тесты проходят
```

---

# DF-020: part_library/view.py

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 3 |
| **Priority** | 🟢 MEDIUM |
| **Зависит от** | [DF-019](./DF-019_part_library_system.md) |
| **Gate** | Gate 3 (частично) |

---

## Подзадачи

- [ ] Таблица деталей:
  - Колонки: SKU, превью SVG (thumbnail), bbox_x × bbox_y мм, mat_type, hole_count, last_seen_at
  - Строка поиска: по SKU (partial) + bbox диапазон (range slider)
  - Кнопка фильтр по материалу (dropdown)
- [ ] Карточка детали (modal):
  - SVG превью (крупное)
  - Метрики: bbox_x/y, contour_count, hole_count, corner_count, weight
  - PartTemplate предупреждения: список с severity бейджами
  - Кнопка "Добавить предупреждение" → форма
  - **Секция "Где эта деталь?"**:
    - Список WorkItem-ов (ссылки + статусы)
    - Список ProductionUnit-ов (label_id + StorageLocation)
- [ ] `lib/widgets/part_preview.py`:
  - `ui.image(svg_path)` если SVG существует
  - Fallback: иконка-заглушка если нет SVG

---

## TDD: Тесты

```python
async def test_part_library_view_renders(mock_sdk):
    view = PartLibraryView(sdk=mock_sdk)
    await view.render()  # smoke test

def test_part_preview_widget_fallback_no_crash(tmp_path):
    widget = PartPreviewWidget(svg_path=None)
    # Должен рендериться без ошибок
    widget.render()
```

---

## Definition of Done

```
✓ Таблица деталей с SVG превью рендерится
✓ Поиск по SKU (partial) работает в реальном времени
✓ Bbox range slider фильтрует правильно
✓ Карточка детали: обратный поиск (WorkItem-ы + ProductionUnit-ы)
✓ PartTemplate: добавление/удаление работает
✓ PartPreview: graceful fallback если нет SVG
```
