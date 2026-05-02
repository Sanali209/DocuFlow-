# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🛠 Build & Development Commands

### Environment Setup
- Install dependencies: `uv sync`
- Update lockfile: `uv lock`

### Running the App
- Start a node: `uv run python -m docuflow.main`
- Start with specific ID/Port:
  ```bash
  export DOCUFLOW_NODE_ID="STATION_A"
  export DOCUFLOW_PORT=8080
  uv run python -m docuflow.main
  ```

### Testing
- Run all tests: `uv run pytest`
- Run specific test file: `uv run pytest tests/unit/test_filename.py`
- Run tests with coverage: `uv run pytest --cov=src`

### Linting & Type Checking
- Lint and fix: `uv run ruff check . --fix`
- Format code: `uv run ruff format .`
- Type checking: `uv run mypy src`

### Diagnostics & Scripts
- Scanner diagnostics: `uv run python scripts/dev/diagnose_scanner.py`
- Check settings: `uv run python scripts/dev/check_settings.py`
- Reset cluster: `uv run python scripts/ops/reset_cluster.py`
- Seed test data: `uv run python scripts/dev/seed_test_data.py`

## 🏗 High-Level Architecture

### Core Principles
- **Symmetric Truth**: No central database. Every node has a local SQLite DB (`{node_id}.db`).
- **File Bus Protocol**: Communication via `REQ_...json` and `RES_...json` files on a shared network path.
- **Master Election**: Cluster role (Leader/Slave) is dynamically elected via heartbeat staleness.
- **Vertical Slices**: Features are organized by functionality in `src/docuflow/features/`.

### Code Structure
- **Entrypoint**: `src/docuflow/main.py` (FastAPI + NiceGUI setup).
- **Application Logic**:
  - `src/docuflow/features/<feature>/`:
    - `view.py`: NiceGUI UI components and page routing.
    - `system.py`: Business logic and feature-specific services.
- **Orchestration**:
  - `src/docuflow/application/bus/orchestrator.py`: P2P Leader election and message dispatching.
  - `src/docuflow/infrastructure/bus.py`: Atomic file operations for the FileBus.
- **Infrastructure**:
  - `src/docuflow/infrastructure/di.py`: DI using **Dishka**. Pay attention to `Scope.APP` vs `Scope.REQUEST`.
  - `src/docuflow/infrastructure/config.py`: Config via pydantic-settings (prefix `DOCUFLOW_`).
- **Domain**:
  - `src/docuflow/domain/entities/`: Core business models (SQLModel).

### Development Patterns
- **Atomic Writes**: Always write to `TEMP_...` then rename to final filename to ensure sync integrity.
- **Immutable Source**: Network files are read-only; never modify files in the shared scan root.
- **NS Mirror**: `NSMirrorService` handles background local caching of network files on all nodes.
- **BaseSystem Lifecycle**: All systems should inherit `BaseSystem` and use `on_startup`/`on_shutdown`.
- **Settings Scopes**: `BaseModuleSettings` uses `scope="local"` (from .env) or `scope="global"` (synced via DB).
- **TDD-First**: Add tests in `tests/` (unit or integration) before implementing new logic.
