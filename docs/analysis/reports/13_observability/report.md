# 13. Наблюдаемость (Observability)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 13.1 Logging

### Loguru Usage
```python
from loguru import logger

logger.info(f"FileBus: Monitoring {self._inbox} for node {self._node_id}")
logger.debug(f"[{self.config.node_id}] Dispatcher: Registered handler for {command}")
logger.trace(f"FileBus: Temp cleanup examined={examined} removed={removed}")
logger.warning(f"Coordination: Takeover from {lock_metadata.get('node_id')}")
logger.error(f"Coordination: CRITICAL - Failed to emit heartbeat")
```

### ✅ Good
- Structured logging with context
- Multiple log levels
- Node ID in messages

---

## 13.2 Log Levels

### Config
```python
# config.py
log_level: str = "INFO"

# constants.py
COORDINATOR_HEARTBEAT_INTERVAL = 15.0
```

### Current Usage
| Level | Usage |
|-------|-------|
| TRACE | Polling, temp cleanup |
| DEBUG | Handler registration |
| INFO | Startup, heartbeats |
| WARNING | Takeovers, issues |
| ERROR | Critical failures |
| EXCEPTION | Stack traces |

---

## 13.3 Health Checks

### ❌ NOT FOUND
- No health endpoint
- No readiness probe
- No liveness check

### ⚠️ Gap
- Kubernetes can't verify health
- No graceful degradation signals

---

## 13.4 Metrics

### KPI Widgets
```python
# lib/widgets/kpi_card.py
class KPICard(ui.label):
    """Reusable KPI display component."""
```

### ✅ Available
- KPI cards in UI
- Status indicators
- Activity stream

### ⚠️ Missing
- Prometheus metrics
- Custom counters
- Latency histograms

---

## 13.5 Tracing

### ❌ NOT FOUND
- No request IDs
- No distributed tracing
- No correlation IDs

### ⚠️ Impact
- Hard to debug multi-node issues
- No performance profiling

---

## 13.6 Log Configuration

### Current
```python
# loguru default
logger.add(sys.stderr, format="{time} {level} {message}")
```

### ⚠️ Issues
- No log rotation
- No structured JSON output
- No output to file

---

## 13.7 Выводы

### ✅ Сильные стороны
- Loguru configured
- Multiple log levels
- Context in messages
- TRACE for debugging

### ⚠️ Проблемы
1. **No health checks** — can't verify status
2. **No metrics** — no quantitative data
3. **No tracing** — hard to debug
4. **No log rotation** — unbounded disk usage
5. **No structured output** — can't parse easily

---

## 13.8 Рекомендации

1. **Add health endpoint**:
   ```python
   @app.get("/health")
   async def health():
       return {"status": "healthy", "node_id": config.node_id}
   ```

2. **Add metrics**:
   ```python
   from prometheus_client import Counter, Histogram
   
   messages_sent = Counter('bus_messages_sent_total', 'Messages sent')
   processing_time = Histogram('message_processing_seconds', 'Processing time')
   ```

3. **Structured logging**:
   ```python
   logger.add(
       "logs/app.log",
       rotation="100 MB",
       retention="30 days",
       format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[node_id]} | {message}"
   )
   ```

4. **Request IDs**:
   ```python
   async def middleware(request, call_next):
       request_id = str(uuid.uuid4())
       request.state.request_id = request_id
       logger.configure(extra={"request_id": request_id})
   ```

---

## 13.9 TODO

- [ ] Add health endpoint
- [ ] Add Prometheus metrics
- [ ] Configure log rotation
- [ ] Add request IDs
- [ ] JSON structured logging

---

*Секция: 13_observability*
