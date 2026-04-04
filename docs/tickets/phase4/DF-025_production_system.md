# DF-025: ProductionSystem (паллеты + складирование)

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 4 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md), [DF-013](../phase2/DF-013_task_board_system.md) |
| **Блокирует** | [DF-026](./DF-026_production_view.md) |
| **Data Flow** | [03_data_flow.md §7](../architecture/03_data_flow.md) |

---

## Контекст

ProductionUnit — паллета с деталями. Создаётся при завершении TaskItem. Human-readable label_id для ввода вручную. Поддерживает split (часть в запас, часть в работу) и merge. Хранит информацию где физически лежат детали.

---

## Execution Plan

```
1. Реализовать generate_human_id() — генератор label_id
2. Реализовать create_unit() — вызывается из DF-013 complete_task()
3. Реализовать split() и merge()
4. Реализовать поиск (live partial по label_id)
5. StorageLocation CRUD
```

---

## Подзадачи

### generate_human_id
- [ ] `generate_human_id(node_code: str) -> str`:
  - Формат: `"{year2d}-{month:02d}-{node_code}-{seq:03d}"`
  - Пример: `"25-07-А-042"`
  - `seq`: следующий порядковый номер для года+месяца+node_code
  - `node_code` берётся из `settings.node_code` (local env)

### ProductionUnit CRUD
- [ ] `create_unit(task_item_id?, qty_produced, node_code, storage_code?, is_pre_system=False, created_by?) -> ProductionUnit`:
  - `label_id = generate_human_id(node_code)`
  - Если `storage_code`: найти или создать StorageLocation
  - `is_pre_system=True` → `task_item_id = None`
- [ ] `get_unit(label_id) -> Optional[ProductionUnit]`
- [ ] `search_units(query: str) -> list[ProductionUnit]`:
  - По partial label_id (live search): `LIKE "%{query}%"`
  - По `sku` через TaskPart
  - По `work_item_id` через TaskItem
- [ ] `update_location(label_id, storage_code)`:
  - Найти или создать StorageLocation
  - `unit.storage_location_id = location.id`

### Split
- [ ] `split(label_id, qty_to_stock: int) -> tuple[ProductionUnit, ProductionUnit]`:
  - `unit_stock` = новая ProductionUnit(qty=qty_to_stock, is_stock=True, parent_label_id=original)
  - `unit_active` = новая ProductionUnit(qty=original.qty - qty_to_stock, is_stock=False, parent_label_id=original)
  - Исходная ProductionUnit → archived (удалить или пометить)

### Merge
- [ ] `merge(label_ids: list[str]) -> ProductionUnit`:
  - Все unit должны иметь одинаковый task_item_id (или is_pre_system)
  - Создать новую unit с суммарным qty
  - Исходные — archived

### StorageLocation CRUD
- [ ] `create_location(code, name?) -> StorageLocation`
- [ ] `list_locations() -> list[StorageLocation]`
- [ ] `get_or_create_location(code) -> StorageLocation`

---

## Псевдокод

```python
class ProductionSystem(BaseSystem):
    
    def generate_human_id(self, node_code: str) -> str:
        """
        Génère un label_id human-readable: "25-07-А-042"
        Threading-safe (использует БД-последовательность).
        """
        now = datetime.now()
        year_short = now.strftime("%y")   # "25"
        month      = now.strftime("%m")   # "07"
        
        # Подсчёт существующих в этом периоде для этого узла
        count = self.session.exec(
            select(func.count(ProductionUnit.id))
            .where(ProductionUnit.label_id.like(f"{year_short}-{month}-{node_code}-%"))
        ).first() or 0
        
        seq = count + 1
        return f"{year_short}-{month}-{node_code}-{seq:03d}"
    
    def create_unit(self, task_item_id: Optional[int], qty_produced: int,
                    node_code: str, storage_code: Optional[str] = None,
                    is_pre_system: bool = False,
                    created_by: Optional[str] = None) -> ProductionUnit:
        label_id = self.generate_human_id(node_code)
        location = (self.get_or_create_location(storage_code)
                    if storage_code else None)
        
        unit = ProductionUnit(
            label_id=label_id,
            task_item_id=task_item_id,
            qty_produced=qty_produced,
            storage_location_id=location.id if location else None,
            is_stock=False,
            is_pre_system=is_pre_system,
            created_by=created_by
        )
        self.session.add(unit)
        self.session.commit()
        return unit
    
    def split(self, label_id: str, qty_to_stock: int
              ) -> tuple[ProductionUnit, ProductionUnit]:
        """
        Разделяет паллету: часть в запас (is_stock=True), остаток в работу.
        Исходная паллета помечается как archived через parent_label_id.
        """
        original = self.session.exec(
            select(ProductionUnit).where(ProductionUnit.label_id == label_id)
        ).first()
        if not original:
            raise ValueError(f"ProductionUnit {label_id} не найдена")
        
        remaining = original.qty_produced - qty_to_stock
        node_code = label_id.split("-")[2]  # "25-07-А-042" → "А"
        
        stock_unit = ProductionUnit(
            label_id=self.generate_human_id(node_code),
            task_item_id=original.task_item_id,
            qty_produced=qty_to_stock,
            is_stock=True,
            parent_label_id=label_id,
            storage_location_id=original.storage_location_id
        )
        active_unit = ProductionUnit(
            label_id=self.generate_human_id(node_code),
            task_item_id=original.task_item_id,
            qty_produced=remaining,
            is_stock=False,
            parent_label_id=label_id,
            storage_location_id=original.storage_location_id
        )
        
        # Архивируем исходную
        original.is_archived = True
        
        self.session.add_all([stock_unit, active_unit])
        self.session.commit()
        return stock_unit, active_unit
```

---

## TDD: Тесты

```python
def test_generate_human_id_format(in_memory_db):
    system = ProductionSystem(session=in_memory_db)
    label = system.generate_human_id(node_code="А")
    # Формат: "25-07-А-001"
    parts = label.split("-")
    assert len(parts) == 4
    assert parts[2] == "А"
    assert parts[3].isdigit()

def test_generate_human_id_sequential(in_memory_db):
    system = ProductionSystem(session=in_memory_db)
    id1 = system.generate_human_id("А")
    system.create_unit(task_item_id=1, qty_produced=10, node_code="А")
    id2 = system.generate_human_id("А")
    seq1 = int(id1.split("-")[-1])
    seq2 = int(id2.split("-")[-1])
    assert seq2 == seq1 + 1

def test_create_unit_pre_system(in_memory_db):
    system = ProductionSystem(session=in_memory_db)
    unit = system.create_unit(
        task_item_id=None, qty_produced=50, node_code="А",
        is_pre_system=True
    )
    assert unit.is_pre_system is True
    assert unit.task_item_id is None

def test_split_creates_two_units(in_memory_db):
    system = ProductionSystem(session=in_memory_db)
    original = system.create_unit(task_item_id=1, qty_produced=100, node_code="А")
    
    stock, active = system.split(original.label_id, qty_to_stock=30)
    
    assert stock.qty_produced == 30
    assert stock.is_stock is True
    assert active.qty_produced == 70
    assert active.is_stock is False
    assert stock.parent_label_id == original.label_id
    assert active.parent_label_id == original.label_id

def test_search_by_partial_label(in_memory_db):
    system = ProductionSystem(session=in_memory_db)
    system.create_unit(task_item_id=1, qty_produced=10, node_code="А")  # "25-07-А-001"
    system.create_unit(task_item_id=2, qty_produced=10, node_code="Б")  # "25-07-Б-001"
    
    results = system.search_units("07-А")
    assert len(results) == 1
    assert "А" in results[0].label_id
```

---

## Definition of Done

```
✓ generate_human_id() возвращает "YY-MM-CODE-SEQ" format
✓ Последовательный номер инкрементируется правильно (не дубль)
✓ create_unit() с is_pre_system=True → task_item_id=None
✓ split() создаёт 2 новые единицы с parent_label_id ссылкой
✓ search_units() по partial label_id работает через LIKE
✓ update_location() переносит паллету к новому StorageLocation
✓ StorageLocation get_or_create работает идемпотентно
✓ Все тесты проходят
```
