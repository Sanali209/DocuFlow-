# 22. Отказоустойчивость (Failover & Recovery)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 22.1 Node Failure

### Detection
```python
# coordination.py
def _is_lock_stale(self, lock_metadata: dict) -> bool:
    last_heartbeat = lock_metadata.get("timestamp", 0)
    age = time.time() - last_heartbeat
    return age > self._timeout_seconds  # 45s

COORDINATOR_TIMEOUT_SECONDS = 45.0
```

### ✅ Implemented
- Heartbeat monitoring
- Staleness detection
- Automatic takeover

---

## 22.2 Recovery Procedures

### Leader Failover
```
1. Heartbeat missed (>45s)
2. Lock file considered stale
3. Follower attempts lock acquisition
4. Atomic rename to claim lock
5. New leader elected
```

### ⚠️ Timeline
- **Detection**: 45s
- **Election**: ~1s (atomic)
- **Total**: ~46s downtime

---

## 22.3 Network Failure

### Handling
```python
# bus.py
try:
    await anyio.Path(temp_path).write_text(json.dumps(payload))
except OSError:
    logger.error("Network write failed")
    # Message lost or retried
```

### ⚠️ Issues
- No retry mechanism
- No offline queue
- Message may be lost

---

## 22.4 Graceful Shutdown

### Implementation
```python
async def on_shutdown(self) -> None:
    self._stop_event.set()
    if self._is_leader:
        await self._release_lock()
    self._observer.stop()
    self._observer.join()
```

### ✅ Good
- Leader step-down
- Lock release
- Observer cleanup

---

## 22.5 Crash Recovery

### Temp File Cleanup
```python
def _cleanup_temp_files(self, older_than_seconds=None):
    # Remove stale TEMP_* files on startup
    GC_STALE_BUS_AGE_SECONDS = 86400  # 24h
```

### ✅ Implemented
- Startup cleanup
- Age-based removal
- Best-effort

---

## 22.6 Data Recovery

### Snapshots
```python
SYNC_SNAPSHOTS_DIR = "SNAPSHOTS"
GC_MAX_SNAPSHOTS_TO_KEEP = 10
```

### ✅ Implemented
- Periodic snapshots
- Retention limit
- Leader-only creation

### ⚠️ Issues
- No point-in-time recovery
- No backup verification
- No restore procedure

---

## 22.7 Выводы

### ✅ Сильные стороны
- Automatic failover
- Graceful shutdown
- Temp file cleanup
- Snapshot retention

### ⚠️ Критические проблемы
1. **60s failover time** — too slow
2. **No offline mode** — requires network
3. **No message retry** — may lose data
4. **No backup/restore** — no disaster recovery
5. **No alerting** — failover not notified

---

## 22.8 Рекомендации

1. **Reduce failover time**:
   ```python
   COORDINATOR_TIMEOUT_SECONDS = 20.0  # From 45
   COORDINATOR_HEARTBEAT_INTERVAL = 5.0  # From 15
   ```

2. **Add offline queue**:
   ```python
   class OfflineQueue:
       async def queue_message(self, msg):
           await aiofiles.open('offline_queue.json', 'a')
       
       async def flush(self):
           # Send queued messages when online
   ```

3. **Add alerting**:
   ```python
   async def on_leader_change(old, new):
       await notification.alert(
           f"Leader changed: {old} -> {new}"
       )
   ```

4. **Backup procedure**:
   ```bash
   # Create backup
   sqlite3 node.db ".backup backup.db"
   ```

---

## 22.9 TODO

- [ ] Reduce failover time
- [ ] Add offline queue
- [ ] Add leader change alerting
- [ ] Document backup procedure
- [ ] Test disaster recovery

---

*Секция: 22_failover*
