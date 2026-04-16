# 20. Бизнес-логика (Business Logic)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 20.1 Domain Entities

### WorkItem Lifecycle
```
NEW → PENDING_CUTS → FOLDER_NO_DOC → DOC_NO_FOLDER
     → REGISTERED → IN_PROGRESS → ON_HOLD/BLOCKED
     → DONE → ARCHIVED/CANCELLED
```

### TaskItem Status
```
PLANNED → IN_PROGRESS → ON_HOLD → DONE/CANCELLED/BLOCKED
```

---

## 20.2 Business Rules

### WorkItem Rules
| Rule | Implementation | Status |
|------|---------------|--------|
| Unique folder_name | `unique=True` index | ✅ |
| Auto status on empty folder | `PENDING_CUTS` | ✅ |
| Status transitions | Enum enforced | ⚠️ Partial |

### TaskItem Rules
| Rule | Implementation | Status |
|------|---------------|--------|
| Belongs to WorkItem | FK | ✅ |
| Priority levels | 0-2 range | ⚠️ Not enforced |
| Urgent flag | Boolean | ✅ |

---

## 20.3 Inventory Rules

### Negative Stock Prevention
```python
# features/inventory/system.py
if current_stock - requested < 0:
    raise InsufficientStockError()
```

### ✅ Implemented
- MaterialAudit trail
- Reservation system
- Stock checks

### ⚠️ Issues
- No optimistic locking
- Race conditions possible

---

## 20.4 Part Library

### SKU Format
```
SKU: {PartCode}-{Version}
Example: ABC-123-A
```

### ✅ Implemented
- Version tracking (A, B, C...)
- Template system

---

## 20.5 Chat/Incidents

### Message Types
- Chat messages (global)
- Incident reports
- Incident resolution

### ✅ Implemented
- Thread support
- File attachments
- Author tracking

---

## 20.6 Scanner Logic

### GNC File Processing
```python
# features/folder_scanner/system.py
async def _discovery_loop(self):
    if self.sdk.orchestrator.is_leader:
        await self._scan_folders()
```

### ✅ Good
- Leader-only scanning
- File hash tracking
- Empty folder detection

---

## 20.7 Выводы

### ✅ Сильные стороны
- Clear status enums
- Negative stock prevention
- Leader-only scanning
- Audit trails

### ⚠️ Проблемы
1. **Status transitions not enforced** — can jump states
2. **No optimistic locking** — race conditions
3. **Priority not validated** — 0-2 not checked
4. **No business invariants** — ad-hoc rules

---

## 20.8 Рекомендации

1. **Enforce transitions**:
   ```python
   class WorkItemStatus(str, Enum):
       ALLOWED_TRANSITIONS = {
           'NEW': ['PENDING_CUTS', 'REGISTERED'],
           'IN_PROGRESS': ['ON_HOLD', 'DONE', 'BLOCKED'],
       }
   ```

2. **Add optimistic locking**:
   ```python
   class WorkItem(BaseEntity, table=True):
       version: int = Field(default=0)
   
   def update(self, new_data):
       result = session.exec(
           select(WorkItem)
           .where(WorkItem.id == self.id)
           .where(WorkItem.version == self.version)
       )
       if not result.first():
           raise OptimisticLockError()
   ```

3. **Business rule validation**:
   ```python
   @validator('priority')
   def validate_priority(cls, v):
       if not 0 <= v <= 2:
           raise ValueError("Priority must be 0, 1, or 2")
       return v
   ```

---

## 20.9 TODO

- [ ] Enforce status transitions
- [ ] Add optimistic locking
- [ ] Validate priority range
- [ ] Document all invariants
- [ ] Add integration tests for rules

---

*Секция: 20_business_logic*
