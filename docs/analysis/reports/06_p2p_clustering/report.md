# 06. P2P Clustering & Orchestration

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 6.1 Architecture Overview

### Components
| Component | File | Responsibility |
|-----------|------|----------------|
| **P2POrchestrator** | `orchestrator.py` | Lifecycle management |
| **CoordinationSystem** | `coordination.py` | Leader election |
| **SecureDispatcher** | `dispatcher.py` | HMAC + sequence validation |

### Orchestrator Startup (orchestrator.py:79-100)
```python
async def on_startup(self) -> None:
    # 0. Bootstrapping sub-systems
    await self._coordination.on_startup()
    await self._bus.on_startup()
    await self._sync.on_startup()
    await self._housekeeping.on_startup()
    
    # Start background loops
    await anyio.sleep(0)  # Yield to event loop
    async with anyio.create_task_group() as tg:
        tg.start_soon(self._coordination.run_coordination_loop)
        tg.start_soon(self._dispatcher.run_dispatch_loop)
        tg.start_soon(self._sync.run_sync_loop)
```

---

## 6.2 Leader Election (CoordinationSystem)

### Algorithm
```
1. Check if lock file exists
2. If not → acquire lock atomically
3. If yes → read metadata
   - If self-owned → refresh heartbeat
   - If stale (>45s) → takeover
   - If valid → not leader
```

### Constants
```python
COORDINATOR_LOCK_FILE = ".coordinator.lock"
COORDINATOR_HEARTBEATS_DIR = "HEARTBEATS"
COORDINATOR_TIMEOUT_SECONDS = 45.0      # Stale threshold
COORDINATOR_STALE_NODE_SECONDS = 60
COORDINATOR_HEARTBEAT_INTERVAL = 15.0
```

### Heartbeat Structure
```json
{
  "node_id": "NODE_A",
  "is_leader": true,
  "timestamp": 1744629123.456,
  "last_active": "2026-04-14 12:45:23",
  "pid": 12345
}
```

### ✅ Strong Points
- **Atomic lock acquisition** — TEMP_ → rename
- **Staleness detection** — 45s timeout
- **Step-down cooldown** — 10s prevent flapping
- **PID tracking** — helps debug

### ⚠️ Potential Issues
- **Split-brain risk** — network partition during election
- **No priority/weight** — first-come-first-served
- **Clock skew** — relies on wall clock
- **No lease renewal** — heartbeat IS the lease

---

## 6.3 SecureDispatcher

### Message Flow
```python
def dispatch(self, message: P2PMessage) -> Any:
    # 1. Signature Verification (HMAC)
    if not self._signer.verify(...):
        raise ValueError("Invalid message signature")
    
    # 2. Sequence Validation (Replay Protection)
    if message.sequence <= self._last_sequences[sender_id]:
        raise ValueError("Duplicate or out-of-order sequence")
    
    # 3. Route to handler
    handler = self._handlers[command]
    
    # 4. Update sequence tracker
    self._last_sequences[sender_id] = message.sequence
```

### ✅ Security Features
- **HMAC-SHA256** — tamper detection
- **Sequence tracking** — replay prevention
- **Timing attack protection** — hmac.compare_digest

### ⚠️ Missing
- **Sequence persistence** — lost on restart
- **Sender whitelist** — any signed message accepted

---

## 6.4 Leader Responsibilities

### Only Leader Does
| Task | System | Interval |
|------|--------|----------|
| **DB Snapshots** | DataSyncSystem | 60s |
| **GC/Stale cleanup** | HousekeepingSystem | 3600s |
| **Folder scanning** | FolderScannerSystem | Per config |

### ✅ Benefits
- Reduces contention
- Single writer for snapshots
- Controlled maintenance windows

### ⚠️ Risks
- **Single point of leadership**
- **No leader re-election during long outages**

---

## 6.5 Polling Configuration

### Intervals (constants.py)
```python
BUS_POLLING_INTERVAL = 5.0           # FileBus message poll
SYNC_CHECK_INTERVAL = 60.0           # DataSync loop
GC_INTERVAL = 3600.0                # Housekeeping
COORDINATOR_HEARTBEAT_INTERVAL = 15.0 # Heartbeat
OBSERVER_POLLING_INTERVAL = 2.0      # FileSystem polling
```

### ⚠️ Performance Concerns
| Interval | Operations/sec (100 nodes) |
|----------|---------------------------|
| 2.0s FileObserver | 50 file ops/sec |
| 5.0s BusPoll | 20 file ops/sec |
| 15.0s Heartbeat | 6.6 file ops/sec |

---

## 6.6 Consistency Model

### CAP Theorem Position
```
CA (Consistency + Availability) on a single site
CP (Consistency + Partition tolerance) during network splits
```

### Trade-offs
- **Eventual consistency** — nodes may have stale data
- **Last-Write-Wins** — timestamps for conflict resolution
- **No distributed transactions** — local ACID only

---

## 6.7 Failover Scenario

### Leader Failure Detection
```
1. Leader stops heartbeating
2. Lock becomes stale after 45s
3. Follower detects staleness
4. Acquires lock atomically
5. New leader elected
6. 60s total failover time
```

### ⚠️ Gaps
- **No dead leader detection** — only heartbeat check
- **No graceful degradation** — follower still serves
- **No notification** — apps not informed of failover

---

## 6.8 FileBus Integration

### Orchestrator → FileBus
```python
# Orchestrator coordinates FileBus
await self._bus.on_startup()  # Start monitoring
await self._bus.send_request(...)  # P2P commands
```

### Shared Network Structure
```
shared_network/
├── BUS/
│   ├── INBOX/
│   └── OUTBOX/
├── HEARTBEATS/
│   ├── node_NODE_A.json
│   └── node_NODE_B.json
├── .coordinator.lock
├── SNAPSHOTS/
└── ...
```

---

## 6.9 Выводы

### ✅ Сильные стороны
- Clean leader election algorithm
- Atomic lock acquisition
- HMAC + sequence security
- Clear leader responsibilities
- Configurable intervals

### ⚠️ Критические проблемы
1. **Sequence lost on restart** — replay possible after crash
2. **No clock sync** — wall clock comparison
3. **No distributed transactions** — eventual consistency only
4. **60s failover time** — may be too long for some use cases
5. **No leader metrics** — observability gap

---

## 6.10 Рекомендации

1. **Persist sequence state**:
   ```python
   # Save to local DB
   SELECT MAX(sequence) FROM processed_messages GROUP BY sender_id
   ```

2. **Add clock skew tolerance**:
   ```python
   MAX_CLOCK_SKEW_SECONDS = 5
   if abs(message.timestamp - now) > MAX_CLOCK_SKEW_SECONDS:
       raise ValueError("Clock skew detected")
   ```

3. **Reduce failover time**:
   ```python
   COORDINATOR_TIMEOUT_SECONDS = 20.0  # From 45
   COORDINATOR_HEARTBEAT_INTERVAL = 5.0  # From 15
   ```

4. **Add leader change notifications**:
   ```python
   async def on_leader_change(self, new_leader_id: str):
       await self._notifications.notify(...)
   ```

---

## 6.11 TODO

- [ ] Persist sequence state to DB
- [ ] Add clock skew tolerance
- [ ] Reduce failover time (configurable)
- [ ] Add leader change events
- [ ] Add P2P metrics/monitoring

---

*Секция: 06_p2p_clustering*
