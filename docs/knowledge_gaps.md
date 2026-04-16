# Information Guide: Architectural Surprises & Knowledge Gaps

This document identifies implementation details in **DocuFlow** that are counter-intuitive, non-standard, or represent deliberate workarounds for decentralized environments.

---

## 1. Infrastructure & P2P Protocols

### 1.1 The `PollingObserver` Surprise (`src/docuflow/infrastructure/bus.py`)
- **Observation**: The system uses `watchdog.observers.polling.PollingObserver` instead of the standard `Observer`.
- **Reasoning**: Standard OS-level file notifications (inotify, FSEvents) are notoriously unreliable over network shares (Samba/CIFS). The `PollingObserver` is a deliberate choice to ensure "Polling Stability" as per the Constitution, even at the cost of slight CPU overhead.
- **Trap**: Do not "refactor" this to a standard observer; it will break decentralized cross-node notifications on many network targets.

### 1.2 Multi-Node Concurrent DBs (`src/docuflow/infrastructure/di.py`)
- **Observation**: The database engine is initialized as `f"{config.node_id}.db"`.
- **Reasoning**: This allows multiple nodes to run from the **same directory** (e.g., during testing or high-availability setups on the same host) without SQLite locking errors. Each node has its own "Symmetric Truth" file, and they converge via the Sync system.
- **Trap**: Using a single `shared.db` for all nodes would result in `Database is locked` errors due to filesystem locking latencies on network drives.

### 1.3 Deterministic HMAC Signing (`src/docuflow/domain/messages.py`)
- **Observation**: `json.dumps(data, sort_keys=True)` is used for signable content.
- **Reasoning**: Python's `dict` order or `json.dumps` output can vary between versions/platforms. To ensure HMAC signatures match across the cluster, the keys must be sorted deterministically before hashing.

---

## 2. Concurrency & Lifecycle

### 2.1 The "Temporary" Task Gap (`src/docuflow/application/bus/orchestrator.py`)
- **Observation**: Line 98: `asyncio.create_task(self._run_orchestration_master())`.
- **Gap**: This violates "Structured Concurrency" (AnyIO principles) and binds the app to the `asyncio` backend.
- **Status**: This is a known, documented "gap" intended for refactoring. The master orchestration loop is currently "floating" rather than being bound to the SDK's global task group.

### 2.2 Symmetric Loop Execution (`src/docuflow/application/bus/orchestrator.py`)
- **Observation**: Every node runs the `_maintenance_worker` loop.
- **Reasoning**: To maintain "Symmetry," all nodes run the same loops, but the payload inside is gated by an `if self._coordination.is_leader` check. This ensures that when a leader dies, any other node can immediately take over the maintenance duty without starting new tasks.

### 2.3 Manual Step-Down Cooldown (`src/docuflow/infrastructure/coordination.py`)
- **Observation**: The `step_down` method uses a `_step_down_until` timestamp.
- **Reasoning**: This prevents "Leadership Ping-Pong," where a node releases a lock and immediately re-acquires it because no other node polled the bus fast enough.

---

## 3. Dependency Injection & Scoping

### 3.1 UI Request-Scoping Gap (`src/docuflow/main.py`)
- **Observation**: NiceGUI pages manually enter Dishka containers: `async with _container() as request_container`.
- **Reasoning**: NiceGUI does not have native Dishka integration like FastAPI. This manual scoping is required to ensure `Session` objects (which are `Scope.REQUEST`) are correctly garbage collected after a UI action.
- **Trap**: Direct access to `_container.get()` for scoped items will result in memory leaks or shared sessions across users.

### 3.2 Inconsistent Admin Sessions (`src/docuflow/features/admin/system.py`)
- **Observation**: `AdminSystem` uses manual `with Session(self._engine)` instead of injected `Session`.
- **Gap**: Unlike the `InventorySystem`, the Admin features bypass the DI-scoped sessions. This is a non-standard "surprising" solution used to ensure thread-safe direct access from background P2P handlers.

---

## 4. Message Integrity

### 4.1 Strict Sequence Enforcement (`src/docuflow/application/bus/dispatcher.py`)
- **Observation**: Messages with `sequence <= last_seq` are rejected.
- **Reasoning**: This is the primary defense against Replay Attacks on an unencrypted File Bus.
- **Gap**: The `_last_sequences` cache is in-memory. After a node reboot, there is a "trust gap" where it might accept replayed old messages until the sequence numbers exceed the previous state.

---

> [!IMPORTANT]
> **Conclusion**: The most critical "Knowledge Gaps" are the **Samba-specific polling stabilization** and the **deterministic signing logic**. Proceeding with standard web-app assumptions (e.g., standard FSEvents or non-sorted JSON) will destabilize the P2P cluster.

---

## 5. Testing & Async Synchronization

### 5.1 SQLite `database is locked` in Async Tests
- **Observation**: During heavy asynchronous unit tests (especially `FolderScannerSystem`), filesystem-backed temporary SQLite databases (`sqlite:///:tmp:`) suffer from aggressive write contention, leading to test flakiness and `OperationalError: database is locked`.
- **Reasoning**: SQLite handles concurrent reads well, but writes require exclusive locks. In async operations without stringent isolation, these locks overlap across event loop contexts.
- **Trap**: Using `NullPool` with filesystem-backed SQLite does not resolve locking because `NullPool` closes connections immediately, causing high IO latency.
- **Solution**: Async testing requires an **in-memory database (`sqlite:///:memory:`) paired strictly with `StaticPool`**. This ensures all connections inside the test event loop share the exact same memory space, completely bypassing filesystem overhead.

### 5.2 Atomic Scoping in Subsystems
- **Observation**: Recursive loops inside production features (e.g., extracting multiple `TaskItems` out of a `WorkItem`) must use distinct, atomic `with Session(self.db_engine)` blocks rather than passing an inherited `Session()`.
- **Reasoning**: A single long-standing session collecting multiple writes before committing holds the database lock open, freezing out background `P2P` sync listeners or other async scanner tasks.
- **Rule**: If a system performs bulk recursive updates, pass the IDs downward, not the ORM objects. Resolve tiny, short-lived sessions inside the loop.

### 5.3 SDK Mock Resolution Leakage
- **Observation**: Tests mocking the `SDK` facade often use `AsyncMock` and `MagicMock`. However, if genuine subsystems (like `ProjectSystem`) are constructed inside `mock_sdk.resolve_system_by_type(...)`, they will try to write to the DB. If passed standard `MagicMock` instances for their constructor parameters, SQLAlchemy/SQLModel will attempt to persist the `MagicMock` type, causing `ProgrammingError`.
- **Trap**: Mismatching dependency mocks via basic `cls == NotificationService` works locally but breaks when imports shadow each other (`AttributeError: emit`). Mock resolution must use `if "NotificationService" in getattr(cls, "__name__", ""):` for robust class string matching across import pathways.
