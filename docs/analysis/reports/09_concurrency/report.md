# 09. Конкурентность (Concurrency)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 9.1 Async Patterns

### Usage: 836 matches
```python
# Async function definitions
async def on_startup(self) -> None
async def on_shutdown(self) -> None
async def send_request(...) -> str
async def poll_messages(...) -> list[dict]
```

### ✅ Good Practices
- **async/await** used consistently
- **anyio** for cross-platform async
- **Task groups** for parallel execution

### ⚠️ Potential Issues
- **Blocking calls in async** — `open()` in `_atomic_write`
- **No async-native file I/O** — using sync `os.fsync()`

---

## 9.2 Task Groups

### P2POrchestrator (orchestrator.py)
```python
async with anyio.create_task_group() as tg:
    tg.start_soon(self._coordination.run_coordination_loop)
    tg.start_soon(self._dispatcher.run_dispatch_loop)
    tg.start_soon(self._sync.run_sync_loop)
```

### ✅ Pattern
- Graceful shutdown via CancelScope
- Parallel task execution
- Error propagation

---

## 9.3 Background Tasks

### Task Lifecycle
```python
class FolderScannerSystem(BaseSystem):
    async def on_startup(self) -> None:
        self._loop_task = asyncio.create_task(self._discovery_loop())
    
    async def on_shutdown(self) -> None:
        self._loop_task.cancel()
```

### ⚠️ Issues
- **No task tracking** — orphans possible
- **No watchdog** — hung tasks not detected
- **Cancelled but not awaited** — cleanup issues

---

## 9.4 Session Management

### DI Session (di.py)
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

### ✅ Pattern
- Context manager pattern
- Auto commit on success
- Auto rollback on failure

### ⚠️ Issues
- **Session per request** — not per operation
- **Async wrapper on sync** — session not truly async

---

## 9.5 Race Conditions

### Potential Areas
1. **FileBus writes** — concurrent writes to same file
2. **Lock acquisition** — coordination race
3. **DB commits** — concurrent modifications

### ✅ Protections
- **Atomic rename** — `os.replace()` is atomic on POSIX
- **SQLite locks** — WAL mode handles concurrency
- **TEMP_ pattern** — prevents partial reads

### ⚠️ Windows-specific
- `os.replace()` not guaranteed atomic on Windows
- SMB/CIFS may not support atomic rename

---

## 9.6 Cancel Scope

### Graceful Shutdown
```python
async def on_startup(self) -> None:
    self._cancel_scope = anyio.CancelScope()
    
async def on_shutdown(self) -> None:
    self._cancel_scope.cancel()
    await self._cancel_scope.__aexit__(None, None, None)
```

### ✅ Pattern
- CancelScope for all background loops
- Graceful termination

---

## 9.7 Выводы

### ✅ Сильные стороны
- Consistent async/await
- Task groups for parallelism
- Proper session management
- Atomic file operations

### ⚠️ Проблемы
1. **Sync file I/O in async** — blocking calls
2. **No task monitoring** — orphan tasks possible
3. **Windows atomicity** — not guaranteed
4. **No cancellation timeout** — indefinite wait
5. **Session not async** — sync wrapper

---

## 9.8 Рекомендации

1. **Use aiocs**:
   ```python
   import aiofiles
   async with aiofiles.open(path, 'wb') as f:
       await f.write(data)
       await f.flush()
   ```

2. **Add task monitoring**:
   ```python
   _running_tasks: set[asyncio.Task] = set()
   
   async def _safe_create_task(coro):
       task = asyncio.create_task(coro)
       _running_tasks.add(task)
       task.add_done_callback(_running_tasks.discard)
       return task
   ```

3. **Cancellation timeout**:
   ```python
   async with anyio.move_on_after(30):
       await shutdown_operation()
   ```

---

## 9.9 TODO

- [ ] Replace sync file I/O with aiofiles
- [ ] Add task monitoring
- [ ] Add cancellation timeouts
- [ ] Verify Windows atomicity

---

*Секция: 09_concurrency*
