# Project Audit: DocuFlow Ecosystem

**Date:** 2026-04-02  
**Status:** Comprehensive Analysis Complete

---

## 1. Core Philosophy (Constitution Alignment)

The project follows the `docs/constitution.md` with high fidelity. Below is the verification of key principles:

- **Symmetric Truth**: 🟢 **Verified**. Every node operates on a local `docuflow.db`. The system synchronizes state via JSON snapshots and File Bus deltas rather than a single remote database.
- **TDD-First**: 🟢 **Verified**. Extensive test suite exists in `tests/`, covering unit, integration, and e2e scenarios. Features like `FileBusSystem` and `CoordinationSystem` have dedicated safety tests.
- **Atomic Progress**: 🟢 **Verified**. The File Bus implementation uses `TEMP_` prefixes and `os.rename` to ensure no partially written messages are ever processed.
- **Polling Stability**: 🟢 **Verified**. The system utilizes `PollingObserver` for file monitoring, specifically chosen for reliability over network shares (Samba/CIFS).
- **Code as Documentation**: 🟢 **Verified**. The codebase uses `loguru` for transparent execution, descriptive naming conventions, and `dishka` for clear dependency injection. Docstrings are present in major infrastructure and domain classes.
- **Hexagonal Architecture**: 🟢 **Verified**. The project is strictly divided into `domain` (logic), `infrastructure` (adapters), and `application` (orchestration/services).

---

## 2. Concept Catalog

### 2.1 Hybrid Node (Dual-Mode)
Every DocuFlow instance is a "Schrödingers Node." It starts as a **Slave (Terminal)** but continuously attempts to become the **Master (Coordinator)**.
- **Lead Election**: Managed by `CoordinationSystem`. Acquisition of `.coordinator.lock` signals leadership.
- **Responsibilities**: 
    - *Common*: Local UI (NiceGUI), local DB operations, message polling.
    - *Leader*: Snapshot generation, stale message cleanup, cluster-wide command broadcasting.

### 2.2 File Bus Protocol
A decentralized communication medium using a shared filesystem.
- **Hierarchy**: `/BUS/INBOX` for requests, `/BUS/OUTBOX` for responses.
- **Atomic Handshake**:
    1. Writer creates `TEMP_REQ_...json`.
    2. Writer renames to `REQ_...json`.
    3. Reader processes and deletes the file.
- **Addressing**: Messages are named `TYPE_FROM_TO_ID.json`, allowing nodes to filter for messages specifically intended for them.

### 2.3 Symmetric Truth & Snapshotting
Consistency is maintained through "Periodic Convergence."
- **Local Truth**: The local SQLite database is the immediate authority for the UI.
- **Snapshots**: The Leader periodically exports the database registry to `SNAPSHOTS/SNAP_{node_id}_{timestamp}.json`.
- **Merging**: Peer nodes apply these snapshots using a **Last-Write-Wins (LWW)** policy based on the `updated_at` field of individual records.

### 2.4 Contextual RBAC (Identity Model)
Authorization is a function of both **Identity** and **Location**.
- **User Permission**: What a person is allowed to do (e.g., `can_edit_tasks`).
- **Workplace Capability**: What a specific machine is capable of (e.g., `inventory` module enabled).
- **Enforcement**: Visual elements in NiceGUI are gated by the intersection of User roles and Workplace settings.

---

## 3. Contradiction Report (Implementation vs. Obsidian Docs)

This section lists factual discrepancies between the intended designs in `docs/obsidian/docuFlow/` and the current Python implementation.

| Feature | Obsidian Concept Design | Current Implementation |
| :--- | :--- | :--- |
| **Snapshot Format** | Full database file (`master_backup.db`) | JSON-based entity registry (`SNAP_...json`) |
| **Snapshot Logic** | `VACUUM INTO` (Full replacement) | Table-by-table LWW Merge (Last-Write-Wins) |
| **Snapshot Naming** | `master_v{version}_{ts}_{id}.db` | `SNAP_{id}_{iso_timestamp}.json` |
| **Node Registry** | Dedicated `/NODES` directory | `HEARTBEATS` directory for node status |
| **File Bus Addressing** | `RES_COORD_LASER1_001.json` | `RES_NODEID_TARGETID_ID.json` (ID is suffix) |
| **Admin Controls** | `REQ_ADMIN_STEP_DOWN.json` | Handled via `P2POrchestrator._handle_force_step_down` |
| **Authentication** | Request-based signature in every file | HMAC Signatures implemented in `P2PMessage` envelope |

---

## 4. Current State Summary

The system is currently in a stable **Iteration 2/3** state. 
- **Infrastructure**: Core P2P protocols (Bus, Coordination, Sync) are fully functional and tested.
- **Domain**: Identity and basic Production models are defined.
- **Application**: The `P2POrchestrator` successfully manages the hybrid lifecycle.
- **Features**: 
    - **Admin**: Basic cluster monitoring and user management.
    - **Inventory**: Basic warehouse views.
    - **Auth**: RBAC-based login and session management.
- **UI**: NiceGUI-based portal with reactive layout and vertical slice navigation.

> [!IMPORTANT]
> The most significant architectural deviation is the use of **JSON Snapshots** instead of **SQLite file backups**. This was likely chosen to allow for more granular conflict resolution (merging) rather than destructive replacement of the local database.
