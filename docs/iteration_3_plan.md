# Implementation Plan - Iteration 3: Secure Domain Orchestration & Identity-Aware Coordination

This iteration transforms the DocuFlow P2P infrastructure into a secure, identity-aware orchestration engine. We will implement a "User + Workplace" authorization model, an HMAC-secured request/response protocol over the File Bus, and an administrative control plane for cluster management.

## User Review Required

> [!IMPORTANT]
> **Architectural Base: "Identity + Point"**: Authorization works at the intersection of **User** (permissions) and **Workplace** (hardware capabilities).
> - **Authoritative Truth**: Managed in `master.db` (Leader node). All administrative changes (new user, permission change) are emitted as `REQ` commands to the bus.
> - **Operational Truth**: Managed in `local.db` (Peer nodes). Peer nodes validate local logins using their latest synchronized state.
> - **Security**: Every P2P message is protected by an **HMAC Signature** using a shared `STORAGE_SECRET`.

> [!WARNING]
> **Clock Synchronization**: While we use a "Last-Write-Wins" policy, we will prioritize **Sequence Numbers** inside signed requests to prevent replay attacks and ensure causal ordering of delta updates.

## Proposed Changes

### Phase 1: Security & Identity Foundation
Establish the core data models and cryptographic signing infrastructure.

#### [NEW] [security.py](file:///d:/github/DocuFlow-/src/docuflow/infrastructure/security.py)
- Implement `HMACSigner` for signing and verifying payload integrity.
- Use `Config.storage_secret` as the shared key.

#### [NEW] [identity.py](file:///d:/github/DocuFlow-/src/docuflow/domain/entities/identity.py)
- Implement SQLModels:
    - `Workplace`: (node_id [index], name, allowed_modules [JSON list]).
    - `Role`: (name, permissions [JSON list]).
    - `User`: (username [unique], password_hash, role_id, allowed_workplaces [JSON list]).

---

### Phase 2: Command-Driven Dispatcher (Delta-Sync)
Transition from full snapshots to granular "Request" (REQ) processing.

#### [NEW] [messages.py](file:///d:/github/DocuFlow-/src/docuflow/domain/messages.py)
- Define `P2PMessage` envelope: `{"sender_id": str, "payload": dict, "signature": str, "sequence": int}`.
- Define `SyncCommand` types: `UPSERT_USER`, `REVOKE_PERMISSIONS`, `FORCE_STEP_DOWN`.

#### [NEW] [dispatcher.py](file:///d:/github/DocuFlow-/src/docuflow/application/bus/dispatcher.py)
- Implement `SecureDispatcher(BaseSystem)`:
    - Verify HMAC signature before processing.
    - Route `payload` to specific domain handlers.
    - Track `last_processed_sequence` per node to detect missing gaps.

---

### Phase 3: Administrative Loop (Master Mode)
Implement the "Master Control" logic for administrative nodes.

#### [MODIFY] [orchestrator.py](file:///d:/github/DocuFlow-/src/docuflow/application/bus/orchestrator.py)
- Integrate `SecureDispatcher`.
- Implement `broadcast_request(command)`: Signs and places a new `REQ` file in the OUTBOX.
- Implement "Force Step Down" logic: Allows a signed command to trigger `CoordinationSystem.on_shutdown()`.

#### [MODIFY] [sync.py](file:///d:/github/DocuFlow-/src/docuflow/infrastructure/sync.py)
- Augment leader logic to emit `UPSERT` commands when administrative entities change, rather than full snapshots.
- Retain periodic full snapshots as "Reconciliation Checkpoints" (Best Practice).

---

### Phase 4: Access Control Logic
Implement the logic for dynamic UI generation.

#### [NEW] [access.py](file:///d:/github/DocuFlow-/src/docuflow/application/access.py)
- Implement `check_access(user, workplace)`: Intersection check.
- Implement `get_active_ui_modules(user, workplace)`: Intersection of Role perms and Workplace modules.

---

## Technical Standards: "Constitution Audit"
1. **Symmetric Truth**: `local.db` remains the immediate source of truth for the local node; it is updated by the Dispatcher upon receiving signed Master requests.
2. **Atomic Progress**: Each Task (e.g. "Workplace Entity", "HMAC Signer") represents a verifiable unit.
3. **Hexagonal Integrity**: Security and Dispatcher logic live in `infrastructure` and `application`, while the `User/Workplace` models live in `domain`.

## Verification Plan

### Automated Tests
- **Security Audit**: Verify that the `SecureDispatcher` rejects messages with tampered signatures or incorrect secret keys.
- **Failover Audit**: Verify that "Force Step Down" command successfully triggers leader transition in an E2E cluster.
- **Auth Audit**: Verify `check_access` correctly identifies permission intersections (Admin vs Operator).

### Manual Verification
- Manually edit a local user and verify that an unauthorized node cannot "trick" the system into giving access without a signed master command.
- Inspect `BUS` files to ensure they are human-readable (json) but cryptographically protected.
