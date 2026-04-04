# AGENTS.md

## Fast orientation
- Product goal: decentralized workshop orchestration over a shared folder (no central DB), with per-node SQLite + file-based sync.
- Ground truth order: code first, then `docs/arhitecture_2/*`, then older docs (`docs/architecture/*`).
- App entrypoint is `src/docuflow/main.py`; startup orchestration is in `src/docuflow/sdk.py` and `src/docuflow/application/bus/orchestrator.py`.

## Architecture map (work where responsibility already lives)
- Use vertical slices in `src/docuflow/features/*`: each feature keeps logic in `system.py` and UI in `view.py`.
- Wire new systems through Dishka in `src/docuflow/infrastructure/di.py` (scope is important: `Scope.APP` vs `Scope.REQUEST`).
- Keep domain entities in `src/docuflow/domain/entities/*`; cross-feature orchestration belongs in SDK/orchestrator layers, not views.
- `main.py` routes NiceGUI pages and resolves feature systems from DI per request scope.

## P2P and file-bus rules you must preserve
- FileBus protocol is filename-driven (`REQ_...json`, `RES_...json`) in `src/docuflow/infrastructure/bus.py`.
- Writes must stay atomic: write to `TEMP_*` then rename (`FileBusSystem._atomic_write`).
- Cluster work loops are background tasks in `P2POrchestrator`: coordination, polling, maintenance.
- Security path: messages are signed/verified via HMAC (`HMACSigner`, `SecureDispatcher`).

## Scanner/sync behavior (common regression zone)
- Folder scanning is leader-only (`FolderScannerSystem._discovery_loop` checks `sdk.orchestrator.is_leader`).
- Scanner idempotency is by DB upsert keys: `WorkItem.folder_name`, `TaskItem.file_path` (relative path from scan root).
- Empty production folders should transition to `PENDING_CUTS` and emit `scan.empty_folder` notification.
- NS mirror runs separately (`src/docuflow/features/folder_scanner/mirror.py`) and compares/copies network vs local NS files.

## Config and environment conventions
- Runtime config is `Config` in `src/docuflow/infrastructure/config.py` with env prefix `DOCUFLOW_`.
- Node DB file is derived from node id in DI (`{node_id}.db`), not fixed `local.db`.
- Shared bus/snapshots paths are derived from `shared_path`; avoid hardcoding absolute machine paths in code.

## Developer workflows that match this repo
- Install deps: `uv sync`
- Run app node: `uv run python -m docuflow.main`
- Run tests (project convention): `uv run pytest`
- Quality checks from `pyproject.toml`: `uv run ruff check .` and `uv run mypy src`
- Useful local diagnostics/scripts: `scripts/diagnose_scanner.py`, `scripts/check_settings.py`, `scripts/reset_cluster.py`, `scripts/seed_test_data.py`

## Project-specific coding expectations
- Keep constants named (tests enforce no magic values patterns; see `tests/test_code_quality.py`).
- Public/provider methods are expected to have docstrings (also enforced in quality tests).
- Prefer small, explicit methods and preserve existing status transitions/enums in domain models.
- For new feature work, add tests under `tests/unit` or relevant integration area before implementation (TDD flow is documented in `docs/tickets/INDEX.md`).

