# Iteration 2 Plan: Full P2P Integration & Orchestration

This iteration focuses on the complete integration of the DocuFlow decentralized infrastructure into a cohesive application lifecycle. We follow the **Hexagonal Architecture** pattern, placing domain logic at the center, with infrastructure as adapters and the SDK as the primary application port.

## 🏗️ Architectural Foundations

- **Symmetric Truth**: Each node's **local database** (SQLite) is the primary source of truth. The "Master" (Leader) coordinates state consistency by publishing snapshots to the shared filesystem.
- **TDD-First**: Every development phase begins with the creation of failure-inducing tests (Unit, Integration, and E2E) that define success criteria.
- **Hexagonal Alignment**:
    - **Domain**: Core entities (`Order`, `Nest`, `Setting`) residing in `docuflow.domain`.
    - **Application**: The `P2POrchestrator` (Use Case) and `DocuFlowSDK` (Facade).
    - **Infrastructure**: Adapters for the File Bus, Coordination, and Data Sync in `docuflow.infrastructure`.
- **Failure Management**: Background loop crashes trigger a logged, graceful shutdown of the entire SDK to maintain cluster integrity.
- **Code as Documentation**: No magic values, shortest possible methods, descriptive naming, and premium Google-style docstrings with examples.

---

## 🛠️ Phase 1: Configuration & TDD Infrastructure

Establish the environment-driven control knobs for the P2P system.

### [Task 1.1] Environment-Driven Polling Configuration
- **Objective**: Move all hardcoded intervals to `.env` and `Config`.
- **TDD**: 
    - [NEW] `tests/test_config_intervals.py`: Verify defaults and `.env` overrides for new intervals.
- **Implementation**:
    - [MODIFY] `infrastructure/config.py`: Add `bus_poll_interval`, `coordination_heartbeat_interval`, `sync_check_interval`, `gc_interval`.
    - [MODIFY] `.env.template`: Document all new interval variables.

### [Task 1.2] E2E Mock Environment
- **Objective**: Create a helper for spawning multiple SDK instances in a single test process for E2E verification.
- **TDD**: 
    - [NEW] `tests/test_e2e_hubs.py`: Verify two SDKs can share the same virtual shared root.

---

## 🚀 Phase 2: The P2P Orchestrator (Application Layer)

Implement the central manager for background tasks using `anyio`.

### [Task 2.1] Orchestrator Skeleton & Lifecycle
- **Objective**: Create the `P2POrchestrator` that manages a `TaskGroup`.
- **TDD**:
    - [NEW] `tests/application/test_orchestrator_lifecycle.py`: Verify tasks start and stop on command.
- **Implementation**:
    - [NEW] `application/bus/orchestrator.py`: `P2POrchestrator` providing `start()` and `stop()`.

### [Task 2.2] Loop Implementation: Coordination & Polling
- **Objective**: Implement the background heartbeats and message polling.
- **TDD**:
    - [NEW] `tests/integration/test_orchestrator_loops.py`: Verify coordination state updates in the background.

### [Task 2.3] Leader-Only Maintenance (Sync & GC)
- **Objective**: Integrate `DataSyncSystem` and `HousekeepingSystem` loops, active only when the node is the Leader.

---

## 🔗 Phase 3: SDK Integration & Failure Propagation

Bind the orchestrator to the SDK lifecycle and implement the "Shutdown on Failure" rule.

### [Task 3.1] SDK Lifespan Alignment
- **Objective**: Update `SDK.on_startup()` and `on_shutdown()` to control the orchestrator.
- **Implementation**:
    - [MODIFY] `sdk.py`: Integrate orchestrator management.

### [Task 3.2] Centralized Error Handling
- **Objective**: Ensure any exception in a background task results in a full SDK shutdown.

---

## 🧪 Phase 4: Final Verification & "Code as Documentation" Audit

### [Task 4.1] E2E Cluster Test
- **Objective**: Simulate a multi-node cluster performing leader election, messaging, and data synchronization.

### [Task 4.2] Documentation & Naming Audit
- **Objective**: Final check for magic values, method length, and Google-style docstring quality.
- **Deliverable**: `docs/iteration_2_plan.md` (Self-reflecting this finalized plan).
