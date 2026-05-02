# 🌊 DocuFlow: Decentralized Factory Orchestration

**DocuFlow** is a robust, peer-to-peer (P2P) workflow and information management system designed for industrial environments where reliable internet access is not guaranteed.

It transforms a simple shared network folder (Samba/CIFS) into a highly reliable, cryptographically secured message bus and state synchronization engine.

---

## 🏗️ Core Architectural Principles

DocuFlow is built on the **"Symmetric Truth"** model as defined in our [Constitution](docs/constitution.md):

1. **Hybrid Nodes**: Every node is identical. Each node is a "Slave" by default but can automatically become the "Leader" (Master) through a dynamic election process.
2. **File Bus Protocol**: Communication happens via atomic file operations (`REQ`/`RES` files) on a shared drive, optimized for the latencies of network shares using `PollingObserver`.
3. **Symmetric Truth**: There is no central database. Every node maintains a local SQLite database, which is synchronized via periodic JSON snapshots and incremental P2P deltas.
4. **Hexagonal Architecture**: Strict separation between Domain logic, Infrastructure adapters, and Application orchestration.
5. **Vertical Slices**: Features are organized into self-contained slices where UI logic (`view.py`) and business logic (`system.py`) live together.

---

## 🛠️ Tech Stack

- **Language**: Python 3.12+ (Async-native)
- **UI Framework**: [NiceGUI](https://nicegui.io/) (High-performance reactive web UI)
- **Application Framework**: FastAPI (Serving as the underlying web host)
- **Dependency Injection**: [Dishka](https://github.com/T0_G0/dishka) (Clean provider-based scoping)
- **Database / ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Concurrency**: AnyIO (Backend-agnostic async orchestration)
- **Security**: HMAC-SHA256 (Message signing and integrity verification)

---

## 🗺️ Project Structure

```text
/src/docuflow/
├── application/           # Orchestration & Cross-system logic
│   └── bus/               # P2P Orchestrator & Dispatcher
├── domain/                # Business entities & P2P message schemas
├── infrastructure/        # Adapters (File Bus, Coordination, Sync, DI)
├── features/              # Vertical Slices
│   ├── task_board/        # Task Board v2: 2 tabs, hierarchy, filters
│   ├── admin/             # Cluster health & Identity management
│   ├── auth/              # RBAC & Session management
│   ├── inventory/         # Decentralized stock tracking
│   ├── folder_scanner/    # GNC file scanning & NS Mirror
│   ├── chat/              # Workshop chat + incidents
│   ├── parts/             # Part library, order cart, rework generation
│   ├── production/        # Pallet tracking (ProductionUnit)
│   ├── reports/           # Jinja2/weasyprint PDF reports
│   ├── analytics/         # KPI metrics & charts
│   ├── consumables/       # Nozzles, lenses, tape tracking
│   ├── notifications/     # Notification templates
│   └── view_presets/      # Saved filter presets
├── lib/widgets/           # Reusable NiceGUI components
└── main.py                # Application entry point & DI setup
```

### Task Board v2 — Unified Production Center

- **2 tabs**: "Производство" (full hierarchy) and "Моя корзина" (operator tasks + handover)
- **Hierarchy**: Project → WorkItem → TaskGroup → TaskItem
- **TaskGroup**: replaces old batch_group, status aggregated from TaskItems
- **ViewState**: expansion state saved in DB per user/view
- **ViewPreset**: saved filter presets
- See [Task Board v2 Design](docs/superpowers/specs/2026-04-28-task-board-v2-design.md)

---

## 🚀 Quick Start

### 1. Requirements
Ensure you have [uv](https://github.com/astral-sh/uv) installed.

### 2. Installation
```bash
uv sync
```

### 3. Running a Node
Set unique node IDs and shared paths via environment variables:
```bash
# Node 1
export DOCUFLOW_NODE_ID="STATION_A"
export DOCUFLOW_SHARED_PATH="./shared_network"
uv run python -m docuflow.main

# Node 2 (In another terminal)
export DOCUFLOW_NODE_ID="STATION_B"
export DOCUFLOW_PORT=8083
uv run python -m docuflow.main
```

---

## 🔒 Security & Reliability

- **Atomic Progress**: All P2P messages are written to `TEMP_` files and atomically renamed to prevent partial reads on network shares.
- **Heartbeat & Failover**: If a Leader node disconnects, a new one is elected within 60 seconds based on heartbeat staleness.
- **Message Integrity**: Every bus message is HMAC-signed. Unauthorized or tampered files are automatically ignored and purged.

---

## 📖 Internal Documentation

- [**Knowledge Gaps**](docs/knowledge_gaps.md): Deep-dive into technical nuances and "unexpected" architectural solutions.
- [**Architecture v2**](docs/arhitecture_2/01_design_document.md): Design doc, application architecture, data flow, C4 diagrams.
- [**Code Audit**](docs/analysis/reports/CODE_AUDIT_2026_PROFESSIONAL.md): Identified duplication patterns and refactoring targets.
- [**Glossary**](docs/glossary.md): Key terms used across codebase and docs.
- [**Constitution**](docs/constitution.md): Coding standards and architectural principles.
