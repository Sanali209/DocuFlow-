# DF-021: ConsumableSystem + view

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 3 |
| **Priority** | 🟢 MEDIUM |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md) |
| **Блокирует** | Gate 3 |
| **Data Flow** | [02_application_architecture.md §3](../architecture/02_application_architecture.md) |

---

## Контекст

Расходники: сопла, линзы, защитные стёкла, скотч, газ. Критический остаток → алерт. Учёт по операциям: use/restock/write_off. Может быть привязан к TaskItem.

---

## Подзадачи

### ConsumableSystem
- [ ] `create_consumable(name, category, unit, min_quantity) -> Consumable`
- [ ] `list_consumables(with_critical=False) -> list[Consumable]`:
  - `with_critical=True` → только у которых `quantity <= min_quantity`
- [ ] `use(consumable_id, qty, task_item_id?, user) -> ConsumableLog`:
  - `quantity -= qty`
  - ConsumableLog(use, qty_delta=-qty, ref_task_item_id=task_item_id)
  - Проверить min_quantity → если `quantity <= min_quantity`: ChatMessage(WARNING, "Критический остаток: {name}")
- [ ] `restock(consumable_id, qty, user) -> ConsumableLog`:
  - `quantity += qty`
  - ConsumableLog(restock, qty_delta=+qty)
- [ ] `write_off(consumable_id, qty, reason, user) -> ConsumableLog`:
  - `quantity -= qty`; ConsumableLog(write_off, qty_delta=-qty, note=reason)
- [ ] `get_log(consumable_id, limit=50) -> list[ConsumableLog]`

### consumables/view.py
- [ ] Таблица расходников:
  - Колонки: name, category, quantity, min_quantity, unit, статус (OK/⚠️ критично)
  - Критические строки: красная подсветка
- [ ] Действия:
  - "Использовано" → диалог (qty, task_item ref?)
  - "Поступление" → диалог (qty)
  - "Списание" → диалог (qty, reason)
- [ ] Лог движений: последние 50 записей

---

## Псевдокод

```python
class ConsumableSystem(BaseSystem):
    
    def use(self, consumable_id: int, qty: int,
            task_item_id: Optional[int], user: str) -> ConsumableLog:
        consumable = self.session.get(Consumable, consumable_id)
        consumable.quantity -= qty
        
        log = ConsumableLog(
            consumable_id=consumable_id,
            operation="use",
            qty_delta=-qty,
            ref_task_item_id=task_item_id,
            author=user
        )
        self.session.add(log)
        
        # Алерт при критическом остатке
        if consumable.quantity <= consumable.min_quantity:
            self._alert_critical(consumable)
        
        self.session.commit()
        return log
    
    def _alert_critical(self, consumable: Consumable) -> None:
        """Создаёт ChatMessage WARNING при критическом остатке."""
        msg = ChatMessage(
            author="system",
            message_type=ChatMessageType.WARNING,
            content=self.notification_svc.render(
                "consumable.critical",
                name=consumable.name,
                qty=consumable.quantity,
                unit=consumable.unit
            ) or f"⚠️ Критический остаток: {consumable.name} = {consumable.quantity} {consumable.unit}"
        )
        self.session.add(msg)
```

---

## TDD: Тесты

```python
def test_use_reduces_quantity(in_memory_db):
    consumable = Consumable(name="Сопло 1.5", quantity=20, min_quantity=5, unit="шт")
    in_memory_db.add(consumable); in_memory_db.commit()
    system = ConsumableSystem(session=in_memory_db)
    
    system.use(consumable.id, qty=3, task_item_id=None, user="user1")
    
    updated = in_memory_db.get(Consumable, consumable.id)
    assert updated.quantity == 17

def test_critical_alert_on_min_reached(in_memory_db):
    consumable = Consumable(name="Линза", quantity=6, min_quantity=5, unit="шт")
    in_memory_db.add(consumable); in_memory_db.commit()
    system = ConsumableSystem(session=in_memory_db)
    
    system.use(consumable.id, qty=2, task_item_id=None, user="user1")  # → 4 = ниже min
    
    msgs = in_memory_db.exec(select(ChatMessage)
                              .where(ChatMessage.message_type == ChatMessageType.WARNING)
                              ).all()
    assert len(msgs) >= 1
    assert "Линза" in msgs[0].content

def test_list_critical_only(in_memory_db):
    system = ConsumableSystem(session=in_memory_db)
    system.create_consumable("OK-item",       unit="шт", min_quantity=5)
    system.create_consumable("Critical-item", unit="шт", min_quantity=5)
    system.use(system.get_by_name("Critical-item").id, qty=10, ...)  # → below min
    
    critical = system.list_consumables(with_critical=True)
    assert len(critical) == 1
    assert critical[0].name == "Critical-item"
```

---

## Definition of Done (Gate 3 ✅)

```
Gate 3 PASSED если (DF-017..DF-021):
  ✓ MaterialSystem: приход/резерв/списание/аудит работают
  ✓ material_stock/view.py: time params редактируются бригадиром
  ✓ PartLibrary: пополняется автоматически из сканера
  ✓ find_by_bbox() с tolerance_pct работает
  ✓ Обратный поиск: SKU → WorkItem-ы + ProductionUnit-ы
  ✓ ConsumableSystem: критический остаток → ChatMessage(WARNING)
  ✓ Все unit тесты проходят (pytest tests/unit/phase3/)
```
