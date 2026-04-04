# Implementation Plan - P2P System & File Bus (Iteration 1)

This plan details the implementation of a decentralized, peer-to-peer (P2P) architecture for the DocuFlow SDK. Based on the documentation in `docs/obsidian` and refined brainstorming, we will implement a "Hybrid Node" model that uses a shared file-based message bus (File Bus) and a symmetric data synchronization strategy.

## Core Architectural Principles

- **Symmetric Truth**: Every node treats its **local database** as the source of truth. The "Master" node acts as a central synchronizer, managing snapshots on the shared filesystem and coordinating broad state consistency.
- **TDD-First**: Every development phase begins with the creation of failure-inducing tests that define the success criteria for the component.
- **Atomic Progress**: Tasks are broken down into the smallest verifiable units to ensure continuous stability.
- **Polling Stability**: We will use a `PollingObserver` for the File Bus to ensure reliable change detection across network (Samba/CIFS) shares.

## Phase 1: Infrastructure & Configuration (Atomic)

**Goal**: Establish a validated configuration layer for distributed nodes.

- [ ] **Task 1.1**: Define Pydantic models for P2P settings (`NODE_ID`, `SHARED_PATH`, `HEARTBEAT_INTERVAL`).
- [ ] **Task 1.2**: Update `Config` to validate these settings from `.env`.
- [ ] **Task 1.3 (TDD)**: Create tests to verify that the SDK fails early if `SHARED_PATH` is missing or inaccessible.

## Phase 2: File Bus System (Atomic)

**Goal**: Create a robust, atomic, file-based messaging interface.

- [ ] **Task 2.1**: Implement the `FileBusSystem` using `anyio` for I/O.
- [ ] **Task 2.2**: Implement atomic write protocol (`TEMP_` -> `os.rename`).
- [ ] **Task 2.3**: Implement `PollingObserver` for cross-platform network stability.
- [ ] **Task 2.4 (TDD)**: Verify message delivery between two virtual nodes in a shared folder.

## Phase 3: Coordination & Leader Election (Atomic)

**Goal**: Implement the dynamic leader election mechanism.

- [ ] **Task 3.1**: Implement `.coordinator.lock` acquisition and renewal logic.
- [ ] **Task 3.2**: Implement the "Heartbeat" task that updates the lock timestamp.
- [ ] **Task 3.3 (TDD)**: Verify that when Node A (Leader) stops its heartbeat, Node B promotes itself after the timeout.

## Phase 4: Symmetric Data Sync (Atomic)

**Goal**: Synchronize local state across the peer network.

- [ ] **Task 4.1**: Add `updated_at` timestamps to all critical entity models.
- [ ] **Task 4.2**: Implement "Master Snapshot" logic (Leader exports local DB to Samba).
- [ ] **Task 4.3**: Implement "Peer Import" logic (Slaves merge Master data based on timestamps).
- [ ] **Task 4.4 (TDD)**: Verify that a change on Node A eventually propagates to Node B via the Master's snapshot.

## Phase 5: Housekeeping & GC

**Goal**: Prevent filesystem bloat and ensure long-term health.

- [ ] **Task 5.1**: Implement time-based cleanup for the `/BUS` folder (managed by the Leader).
- [ ] **Task 5.2**: Implement log rotation for the `/LOGS` network folder.

## Environment Template (.env)

```properties
APP_NAME=DocuFlow_Laser_01
NODE_ID=LASER_01
# Path to shared network resource (use local mock for dev)
SHARED_PATH=./shared_network
DATABASE_URL=sqlite:///./local.db
HEARTBEAT_INTERVAL=15
COORDINATOR_TIMEOUT=45
LOG_LEVEL=INFO
```

---

## Open Questions

- **Sync Frequency**: How often should the Leader create snapshots? (Proposed: Every 60 seconds or after 50 local changes).
- **Conflict Handling**: Is simple "Last-Write-Wins" sufficient for all entities?
