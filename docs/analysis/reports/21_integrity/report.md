# 21. Целостность данных (Data Integrity)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 21.1 Consistency Checks

### DB Integrity
```python
# di.py
cursor.execute("PRAGMA foreign_keys=ON")
```

### ✅ Enabled
- Foreign keys enforced
- Referential integrity

### ⚠️ Issues
- No periodic integrity checks
- No consistency validation

---

## 21.2 NS Mirror

### Functionality
```python
# features/folder_scanner/mirror.py
class NSMirrorService:
    async def _sync_bucket(self, settings: FolderScannerSettings):
        # Compare network vs local files
        # Copy missing files
        # Log mismatches
```

### ✅ Implemented
- Network vs local sync
- Missing file detection
- Mismatch logging

---

## 21.3 Data Sync

### Snapshot System
```python
# infrastructure/sync.py
SYNC_SNAPSHOTS_DIR = "SNAPSHOTS"
SYNC_PREFIX_SNAP = "SNAP_"
SYNC_CHECK_INTERVAL = 60.0
```

### ✅ Implemented
- Periodic snapshots
- Leader-only creation
- Snapshot directory

---

## 21.4 Audit Trails

### MaterialAudit
```python
class MaterialAudit(BaseEntity, table=True):
    """Tracks all material stock changes."""
    stock_item_id: int = Field(foreign_key="materialstock.id")
    change_type: str  # RECEIVED, USED, ADJUSTED
    quantity: int
    reason: str | None
```

### ✅ Implemented
- Change tracking
- Quantity delta
- Reason recording

---

## 21.5 Reconciliation

### ❌ NOT FOUND
- No reconciliation process
- No data validation

### ⚠️ Risk
- Drift between nodes
- Inconsistent state

---

## 21.6 Transaction Boundaries

### Current
```python
@provide(scope=Scope.REQUEST)
async def get_session(self, engine: Engine) -> AsyncIterable[Session]:
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
```

### ✅ Good
- Auto commit
- Auto rollback
- Clear boundaries

---

## 21.7 Выводы

### ✅ Сильные стороны
- Foreign keys enabled
- NS Mirror implemented
- Audit trails exist
- Transaction per request

### ⚠️ Проблемы
1. **No integrity checks** — corruption undetected
2. **No reconciliation** — drift possible
3. **No validation** — invalid data accepted
4. **Eventual consistency only** — conflicts resolved by LWW

---

## 21.8 Рекомендации

1. **Periodic integrity check**:
   ```python
   async def integrity_check():
       result = session.exec("PRAGMA integrity_check")
       if result != ['ok']:
           logger.error(f"DB integrity issue: {result}")
   ```

2. **Reconciliation job**:
   ```python
   async def reconcile():
       # Compare node states
       # Detect drift
       # Log discrepancies
   ```

3. **Cross-node validation**:
   ```python
   # Compare snapshot hashes
   SNAPSHOT_HASH = sha256(serialized_db)
   ```

---

## 21.9 TODO

- [ ] Add periodic integrity check
- [ ] Implement reconciliation
- [ ] Add cross-node validation
- [ ] Monitor consistency metrics
- [ ] Document conflict resolution

---

*Секция: 21_integrity*
