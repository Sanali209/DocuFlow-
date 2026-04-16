# 10. Производительность (Performance)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 10.1 Database Performance

### SQLite Optimizations
```python
# di.py:105-117
cursor.execute("PRAGMA journal_mode=WAL")       # Concurrent reads
cursor.execute("PRAGMA synchronous=NORMAL")      # Reduced sync
cursor.execute("PRAGMA foreign_keys=ON")        # Integrity
cursor.execute("PRAGMA cache_size=-64000")       # 64MB cache
```

### ✅ Good Settings
- WAL mode for concurrency
- 64MB cache
- Synchronous NORMAL balance

### ⚠️ Missing
- Memory-mapped I/O (`PRAGMA mmap_size`)
- `PRAGMA temp_store=MEMORY`
- Query optimization

---

## 10.2 Polling Impact

### Current Intervals
```python
OBSERVER_POLLING_INTERVAL = 2.0  # FileSystem polling
BUS_POLLING_INTERVAL = 5.0     # Message polling
HEARTBEAT_INTERVAL = 15.0       # Leader heartbeat
SYNC_CHECK_INTERVAL = 60.0      # Data sync
GC_INTERVAL = 3600.0           # Garbage collection
```

### ⚠️ Resource Usage
| Interval | Ops/100 nodes/min |
|----------|-------------------|
| 2.0s FileObserver | 3000 scans |
| 5.0s BusPoll | 1200 polls |

---

## 10.3 N+1 Queries

### Potential Issue
```python
for work_item in work_items:
    print(work_item.project.name)  # N+1
    for task in work_item.tasks:
        print(task.material_type)  # N+1
```

### ✅ Mitigation
- SQLModel relationships
- Lazy loading used

### ⚠️ Risk
- No eager loading found
- Batch operations limited

---

## 10.4 Memory

### Large Objects
- **JSON messages** — no size limit
- **File reads** — entire file in memory
- **Chat messages** — unbounded list

### ⚠️ Concerns
- No streaming for large files
- No pagination in lists
- No cache eviction

---

## 10.5 Network

### FileBus Overhead
```python
# bus.py:297
data = json.dumps(payload, indent=2).encode("utf-8")
```

### ⚠️ Issues
- `indent=2` — larger JSON size
- No compression
- Polling overhead

---

## 10.6 UI Performance

### NiceGUI Updates
```python
# Watchdog-based updates
ui.timer(1.0, update_callback)
```

### ⚠️ Issues
- Polling-based UI updates
- No debouncing
- Full re-renders

---

## 10.7 Выводы

### ✅ Сильные стороны
- WAL mode for concurrency
- 64MB SQLite cache
- Atomic writes

### ⚠️ Проблемы
1. **Polling overhead** — too frequent
2. **No query optimization** — N+1 possible
3. **No compression** — JSON bloat
4. **No pagination** — unbounded lists
5. **Polling UI** — inefficient updates

---

## 10.8 Рекомендации

1. **Optimize polling**:
   ```python
   OBSERVER_POLLING_INTERVAL = 5.0  # From 2.0
   BUS_POLLING_INTERVAL = 10.0      # From 5.0
   ```

2. **Eager loading**:
   ```python
   select(WorkItem).options(
       joinedload(WorkItem.project),
       joinedload(WorkItem.tasks)
   )
   ```

3. **Pagination**:
   ```python
   session.exec(
       select(ChatMessage)
       .order_by(ChatMessage.created_at.desc())
       .limit(50)
   )
   ```

4. **JSON compression**:
   ```python
   import gzip
   data = gzip.compress(json.dumps(payload).encode())
   ```

---

## 10.9 TODO

- [ ] Increase polling intervals
- [ ] Add eager loading
- [ ] Implement pagination
- [ ] Add JSON compression
- [ ] Profile hot paths

---

*Секция: 10_performance*
