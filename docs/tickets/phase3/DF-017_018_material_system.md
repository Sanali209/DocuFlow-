# DF-017: MaterialSystem + Аудит

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 3 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md) |
| **Блокирует** | [DF-018](./DF-018_material_stock_view.md), [DF-013](../phase2/DF-013_task_board_system.md) (write_off) |
| **Data Flow** | [03_data_flow.md §8](../architecture/03_data_flow.md) |

---

## Контекст

Полный учёт движений листового металла: приход, резерв, списание, коррекция. Мастер данных — MaterialType с параметрами для estimate_time. Все движения фиксируются в MaterialAudit для трассировки.

---

## Подзадачи

### MaterialType CRUD
- [ ] `create_type(code, form_factor, thickness?, nominal_x?, nominal_y?, **time_params)`
- [ ] `update_time_params(mat_type_id, cut_speed?, pierce_time?, idle_speed?, tolerance?)`
  - Бригадир корректирует params когда видит drift%
- [ ] `list_types(filters) -> list[MaterialType]`

### MaterialStock CRUD
- [ ] `receive_stock(mat_type_id, qty, batch_code?, location?) -> MaterialStock`:
  - Создать MaterialStock(status=AVAILABLE)
  - MaterialAudit(income, qty_delta=+qty)
- [ ] `list_stock(mat_type_id?) -> list[MaterialStock]`
- [ ] `get_available(mat_type_id, min_qty) -> list[MaterialStock]` — для резерва

### Reservation
- [ ] `reserve(stock_item_id, work_item_id, qty, type=soft) -> Reservation`:
  - Мягкий (soft): MaterialStock.status остаётся AVAILABLE
  - Жёсткий (hard): MaterialStock.status → RESERVED
- [ ] `release_reservation(reservation_id)`:
  - Удалить Reservation
  - Если hard: MaterialStock.status → AVAILABLE
- [ ] `get_reservations(work_item_id) -> list[Reservation]`

### Списание (write_off) — вызывается из DF-013
- [ ] `write_off(task_item: TaskItem, sheets_used: int, author: str)`:
  - Найти Reservation для work_item (или первый available по mat_type)
  - MaterialAudit(write_off, qty_delta=-sheets_used, ref_task_item_id=task_item.id)
  - Обновить MaterialStock.quantity

### Дозаказ
- [ ] `request_reorder(mat_type_id, qty, note, author) -> ChatMessage`:
  - MaterialAudit(reorder, note=note)
  - ChatMessage(type=ORDER, content=note, ref=None)

### Инвентаризация
- [ ] `inventory_correction(stock_item_id, actual_qty, reason, author)`:
  - delta = actual_qty - stock.quantity
  - MaterialAudit(correction, qty_delta=delta, reason=reason)
  - stock.quantity = actual_qty

---

## Псевдокод

```python
class MaterialSystem(BaseSystem):
    
    def write_off(self, task_item: TaskItem, sheets_used: int, author: str) -> None:
        """
        Списание материала при завершении TaskItem.
        Ищет Reservation или берёт первый AVAILABLE батч.
        """
        mat_type_id = task_item.mat_type_id
        if not mat_type_id:
            return  # Нет материала — нет списания
        
        # Найти резерв под work_item
        reservation = self.session.exec(
            select(Reservation)
            .where(Reservation.work_item_id == task_item.work_item_id)
            .where(Reservation.stock_item.has(
                MaterialStock.mat_type_id == mat_type_id))
        ).first()
        
        if reservation:
            stock = reservation.stock_item
            if reservation.type == "hard":
                self.release_reservation(reservation.id)
        else:
            # FIFO: первый available
            stock = self.session.exec(
                select(MaterialStock)
                .where(MaterialStock.mat_type_id == mat_type_id)
                .where(MaterialStock.status == MaterialStockStatus.AVAILABLE)
                .order_by(MaterialStock.created_at)
            ).first()
        
        if stock:
            stock.quantity -= sheets_used
            audit = MaterialAudit(
                stock_item_id=stock.id,
                operation="write_off",
                qty_delta=-sheets_used,
                ref_task_item_id=task_item.id,
                author=author,
                node_id=self.sdk.config.node_id
            )
            self.session.add(audit)
            self.session.commit()
```

---

## TDD: Тесты

```python
def test_receive_creates_stock_and_audit(in_memory_db):
    mat = MaterialType(id=1, code="ST37-3mm")
    system = MaterialSystem(session=in_memory_db)
    stock = system.receive_stock(mat_type_id=1, qty=20, batch_code="2025-07")
    
    assert stock.quantity == 20
    assert stock.status == MaterialStockStatus.AVAILABLE
    audits = in_memory_db.exec(select(MaterialAudit)).all()
    assert len(audits) == 1
    assert audits[0].qty_delta == 20

def test_write_off_reduces_stock(in_memory_db):
    stock = MaterialStock(mat_type_id=1, quantity=10, status=AVAILABLE)
    task = TaskItem(mat_type_id=1, work_item_id=1, ...)
    system = MaterialSystem(...)
    system.write_off(task, sheets_used=3, author="system")
    
    updated = in_memory_db.get(MaterialStock, stock.id)
    assert updated.quantity == 7

def test_hard_reservation_locks_stock(in_memory_db):
    stock = MaterialStock(status=AVAILABLE, ...)
    system = MaterialSystem(...)
    system.reserve(stock.id, work_item_id=1, qty=5, type="hard")
    
    updated = in_memory_db.get(MaterialStock, stock.id)
    assert updated.status == MaterialStockStatus.RESERVED

def test_reorder_creates_chat_message(in_memory_db):
    system = MaterialSystem(...)
    system.request_reorder(mat_type_id=1, qty=50, note="Срочно!", author="user1")
    
    msgs = in_memory_db.exec(select(ChatMessage)).all()
    assert any(m.message_type == ChatMessageType.ORDER for m in msgs)
```

---

## Definition of Done

```
✓ receive_stock() создаёт MaterialStock + MaterialAudit
✓ write_off() списывает правильное кол-во листов
✓ Hard reservation блокирует статус
✓ Release reservation → возвращает AVAILABLE
✓ request_reorder() создаёт ChatMessage(ORDER)
✓ inventory_correction() аудируется с delta
✓ Все тесты проходят
```

---

# DF-018: material_stock/view.py

## Метаданные

| **Phase** | 3 | **Priority** | 🟢 MEDIUM |
|---|---|---|---|
| **Зависит от** | [DF-017](./DF-017_material_system.md) | **Блокирует** | Gate 3 (частично) |

---

## Подзадачи

- [ ] Типы материалов:
  - Таблица: code, form_factor, thickness, остаток, статус
  - Редактирование time params (cut_speed, pierce_time, оленьи скорости, tolerance%)
  - Подсветка dtype который часто даёт высокий drift%
- [ ] Остатки:
  - По каждому типу: доступно / зарезервировано / всего
  - Лог движений (MaterialAudit) с фильтром
  - Кнопка "Приход" → диалог (qty, batch_code, location)
  - Кнопка "Инвентаризация" → диалог (actual_qty, reason)
  - Кнопка "Дозаказ" → диалог → ChatMessage(ORDER)
- [ ] Резервы:
  - Список активных резервов под активные наряды
  - Кнопка "Освободить резерв" (если наряд отменён)

---

## Definition of Done

```
✓ Таблица типов материалов + редактирование time params
✓ Кнопки Приход/Инвентаризация/Дозаказ работают
✓ Аудит-лента движений виджет
✓ Дозаказ → ChatMessage(ORDER) создаётся
```
