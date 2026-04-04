# Core Architecture: SDK & Module Concepts

This document outlines the foundational design patterns used in the DocuFlow ecosystem to ensure a robust, maintainable, and decentralized P2P cluster.

---

## 1. SDK Facade & Lifecycle

The **SDK** (`src/docuflow/sdk.py`) serves as the single entry point for the entire ecosystem. It encapsulates the complexity of the **Dishka** Dependency Injection (DI) container.

### Key Responsibilities:
- **Unified Gateway**: Provides a stable API for application layers (UI, CLI) to resolve internal systems.
- **Hot Boot Orchestration**: Manages the `on_startup` and `on_shutdown` hooks, ensuring the P2P cluster (Orchestrator, Bus, Coordination) initializes in the correct order.
- **Resource Allocation**: Shortens the loop between the underlying DI container and the domain logic.

---

## 2. BaseSystem & Modules

Every service in DocuFlow inherits from `BaseSystem` (`src/docuflow/application/base.py`).

- **BaseSystem**: Standardizes how systems access "Cold Boot" configuration (e.g., paths and credentials) and provides asynchronous lifecycle hooks.
- **Subsystems**: Infrastructure (File Bus, Sync) and Application (Inventory, Admin) layers are built as modular systems that are easy to test and replace.

---

## 3. GUI Vertical Slices

To maintain high cohesion and low coupling, DocuFlow uses the **Vertical Slice** pattern for its feature modules (located in `src/docuflow/features/`).

### Folder Structure:
```text
/features/inventory/
├── __init__.py
├── system.py      # Business Logic & P2P Synchronization
└── view.py        # NiceGUI User Interface
```

### Pattern Logic:
- **High Cohesion**: The UI (`view.py`) and its corresponding business logic (`system.py`) live in the same directory.
- **Separation of Concerns**: `system.py` handles the "Truth" (Database, P2P commands), while `view.py` handles the "Display" (NiceGUI layout, reactive state).
- **Maintenance**: Developers can find everything related to a specific feature in one place, avoiding "shotgun surgery" across the codebase.

---

## 4. Declarative P2P Settings

DocuFlow modules can declare their own configuration parameters using a decentralized registry (`src/docuflow/domain/settings.py`).

### Mechanisms:
- **Pydantic Schemas**: Modules define their settings as classes inheriting from `BaseModuleSettings`.
- **Visibility Scopes**:
    - `global`: Synchronized across all nodes via the cluster state.
    - `local`: Specific to the hardware or environment of the current node.
- **Automatic Registration**: Modules use `registry.register()` to expose their configuration to the **Admin Control Plane** for real-time cluster introspection and validation.

---

> [!TIP]
> This modular approach allows DocuFlow to evolve from a single-node application to a complex factory cluster without architectural redesign.
