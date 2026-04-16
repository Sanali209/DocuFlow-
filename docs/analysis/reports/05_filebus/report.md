# 05. FileBus Protocol

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 5.1 Protocol Overview

### File-Based P2P Messaging
```
shared_network/
├── BUS/
│   ├── INBOX/       # Входящие сообщения
│   └── OUTBOX/     # Исходящие сообщения
├── HEARTBEATS/     # Leader election
├── SNAPSHOTS/      # DB snapshots
└── ...
```

### Message Types
| Prefix | Direction | Purpose |
|--------|-----------|---------|
| `REQ_{FROM}_{TO}_{ID}.json` | INBOX | Запросы |
| `RES_{FROM}_{TO}_{ID}.json` | OUTBOX | Ответы |
| `BROADCAST_{FROM}_{ID}.json` | INBOX | Широковещательные |

---

## 5.2 Atomic Write Implementation

### Pattern: TEMP_ → atomic rename

```python
# bus.py:290-321
async def _atomic_write(self, target_dir, filename, payload):
    temp_path = target_dir / f"TEMP_{filename}"
    final_path = target_dir / filename
    
    # 1. Write to temp file
    with open(temp_path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    
    # 2. Atomic rename (safer than rename)
    os.replace(temp_path, final_path)
```

### ✅ Преимущества
- **Network crash safety** — читатель не увидит partial write
- **fsync()** — гарантирует запись на диск
- **Fallback fsync** — логирует ошибку, но не падает

### ⚠️ Платформенные нюансы
- `os.replace()` — атомарно на Windows (>=Vista)
- Network share behavior может отличаться

---

## 5.3 Message Structure

### Header
```json
{
  "header": {
    "from": "NODE_A",
    "to": "NODE_B",
    "id": "1744629123456",
    "cmd": "sync_request",
    "timestamp": 1744629123.456
  },
  "body": { ... }
}
```

### Filename Convention
```
REQ_NODE_A_NODE_B_1744629123456.json
{TYPE}_{FROM}_{TO}_{TIMESTAMP}.{EXT}
```

---

## 5.4 HMAC Signing

### HMACSigner (security.py)
```python
class HMACSigner:
    def sign(self, payload: str) -> str:
        return hmac.new(
            self._secret_bytes,
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
    
    def verify(self, payload: str, signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)
```

### ✅ Security Features
- **HMAC-SHA256** — криптографическая подпись
- **compare_digest** — защита от timing attacks
- **UTF-8 encoding** — consistent encoding

### ⚠️ Missing
- **Message freshness** — нет проверки timestamp
- **Replay protection** — подпись не включает timestamp

---

## 5.5 Polling Observer

### Configuration (constants.py)
```python
OBSERVER_POLLING_INTERVAL = 2.0  # seconds
BUS_POLLING_INTERVAL = 5.0       # seconds
```

### InboxHandler
```python
class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(...)
        if self._is_valid_new_message(filename):
            logger.trace(f"FileBus: Valid new message detected: {filename}")
```

### ✅ Design
- **PollingObserver** — стабильность на network shares
- **FileSystemEventHandler** — фильтрация
- **Ignore TEMP_* files** — только finalized

### ⚠️ Performance
- Polling каждые 2 секунды
- На 100 узлах = 50 ops/sec minimum
- Нет batch processing

---

## 5.6 Message Filtering

### Validation Logic (bus.py:256-280)
```python
def _is_relevant_message(self, filename, folder_name) -> bool:
    # 1. Check extension
    if not filename.endswith(".json"):
        return False
    
    # 2. Ignore TEMP_ files
    if filename.startswith("TEMP_"):
        return False
    
    # 3. Broadcasts for everyone
    if folder_name == INBOX and filename.startswith("BROADCAST_"):
        return True
    
    # 4. Unicast — check {TO} matches our node_id
    is_addressed_to_me = (
        f"_{self._node_id}_" in filename
    )
```

### ⚠️ Potential Issues
- Underscore collision: `MY_NODE_ID` vs `NOT_MY_NODE`
- Case sensitivity на разных OS

---

## 5.7 Cleanup & GC

### Stale File Cleanup (bus.py:215-254)
```python
def _cleanup_temp_files(self, older_than_seconds=None):
    # Cleanup TEMP_* files older than 24h (default)
    GC_STALE_BUS_AGE_SECONDS = 86400
```

### ⚠️ Problems
- Cleanup only on startup
- No continuous cleanup
- No retry for locked files

---

## 5.8 Reliability

### Error Handling
| Operation | Strategy |
|-----------|----------|
| Read | Return None, log exception |
| Write | Delete temp file, re-raise |
| fsync | Log trace, continue |
| Delete | missing_ok=True |

### ✅ Good Practices
- **Async file I/O** — via anyio.Path
- **Graceful degradation** — continue on errors
- **Structured logging** — trace level for debugging

### ⚠️ Missing
- **Retry logic** — no automatic retry
- **Dead letter handling** — failed messages lost
- **Circuit breaker** — no protection from cascades

---

## 5.9 Constants

### FileBus Constants (constants.py)
```python
BUS_DIR_NAME = "BUS"
BUS_INBOX_DIR = "INBOX"
BUS_OUTBOX_DIR = "OUTBOX"
BUS_TEMP_PREFIX = "TEMP_"
BUS_EXTENSION = ".json"
BUS_PREFIX_REQ = "REQ_"
BUS_PREFIX_RES = "RES_"
BUS_PREFIX_BROADCAST = "BROADCAST_"
BUS_DELIMITER = "_"

OBSERVER_POLLING_INTERVAL = 2.0
BUS_POLLING_INTERVAL = 5.0
```

---

## 5.10 Выводы

### ✅ Сильные стороны
- Atomic writes с fsync
- HMAC-SHA256 signing
- Structured message format
- Good error handling
- Constants centralized

### ⚠️ Критические проблемы
1. **No replay protection** — signature не включает timestamp
2. **No message freshness check** — old messages accepted
3. **Polling overhead** — 2s interval may be too frequent
4. **No retry/dead letter** — failed writes lost
5. **Filename underscore collision** — possible false matches

---

## 5.11 Рекомендации

1. **Добавить timestamp в подпись**:
   ```python
   def sign(self, payload: str, timestamp: float) -> str:
       data = f"{payload}:{timestamp}"
       return hmac.new(..., data.encode(), hashlib.sha256).hexdigest()
   ```

2. **Проверять freshness**:
   ```python
   MAX_MESSAGE_AGE_SECONDS = 300  # 5 minutes
   if time.time() - header["timestamp"] > MAX_MESSAGE_AGE_SECONDS:
       return None  # discard old message
   ```

3. **Batch polling**:
   ```python
   # Process multiple messages per poll
   messages = await self.poll_messages()
   for msg in messages:
       await self._process_message(msg)
   ```

4. **Retry logic**:
   ```python
   @async_retry(max_attempts=3, delay=1.0)
   async def _atomic_write(...):
       ...
   ```

---

## 5.12 TODO

- [ ] Добавить timestamp в HMAC signature
- [ ] Проверять message freshness
- [ ] Рассмотреть batch processing
- [ ] Добавить retry logic
- [ ] Исправить underscore collision

---

*Секция: 05_filebus*
