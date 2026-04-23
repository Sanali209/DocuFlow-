# AGENTS.md

## Quick orientation
- **Product**: decentralized workshop orchestration over a shared folder (no central DB), per-node SQLite + file-based sync
- **Ground truth order**: code → `docs/architecture_2/*` → older docs
- **App entrypoint**: `src/docuflow/main.py`; startup orchestration: `src/docuflow/sdk.py`, `src/docuflow/application/bus/orchestrator.py`

## Repository structure
```
DocuFlow/
├── src/                        # Ground-truth source code
├── tests/                      # Strictly categorized — no loose test_*.py in root
│   ├── unit/                   # domain, features, infrastructure, lib
│   ├── integration/
│   ├── e2e/                    # Playwright
│   ├── smoke/
│   ├── ui/
│   ├── application/
│   ├── conftest.py, helpers.py
├── docs/                       # One doc = one subfolder by purpose
│   ├── arhitecture_2/          # Current architecture docs (v7)
│   ├── analysis/               # Audit plan + categorized reports
│   ├── Review/                 # Release reports, reviews
│   ├── Bug track/              # Bug hunts, quick reports
│   └── obsidian/               # Conceptual design vault
├── scripts/                    # Categorized by purpose
│   ├── dev/                    # seed_test_data, diagnose_scanner, check_settings
│   ├── ops/                    # reset_cluster, port_killer, verify_guards
│   └── test/                   # test_startup, test_sqlite_wal
├── assets/fixtures/            # Test data (GNC samples, etc.)
├── static/                     # NiceGUI static assets
├── config/                     # .env.template
├── AGENTS.md, CLAUDE.md, README.md
└── pyproject.toml, pytest.ini, Dockerfile
```
**Rules**: root contains only manifests/configs. No `.db`, `.log`, loose `.py` scripts, or IDE/agent directories in root.
- Runtime artifacts go to `.gitignore` (see `.claude/`, `.idea/`, `test_shared/`, `tmp_shared/`, `*.db`, `app_*.log`, etc.)
- Historical archive: `._archive/` (old prototypes, do not import into src)

## Developer commands
```bash
uv sync                        # install deps
uv run python -m docuflow.main  # run app node
uv run pytest                  # run tests
uv run ruff check . --fix      # lint
uv run ruff format .           # format
uv run mypy src                # typecheck
uv run python scripts/dev/diagnose_scanner.py  # scanner diagnostics
uv run python scripts/dev/check_settings.py   # check settings
uv run python scripts/ops/reset_cluster.py     # reset cluster state
uv run python scripts/dev/seed_test_data.py    # seed test data
uv run python scripts/ops/port_killer.py       # kill process on DOCUFLOW_PORT
```

## Architecture map
- **Vertical slices**: `src/docuflow/features/<feature>/` — each has `system.py` (logic) and `view.py` (UI)
- **DI wiring**: `src/docuflow/infrastructure/di.py` — watch `Scope.APP` vs `Scope.REQUEST`
- **Domain entities**: `src/docuflow/domain/entities/*`
- **Cross-feature orchestration**: SDK / orchestrator layers, not views
- **`main.py`**: routes NiceGUI pages, resolves systems from DI per request scope via `system_scope()` context manager

## Critical P2P/file-bus rules
- FileBus protocol is filename-driven: `REQ_...json`, `RES_...json`, `BROADCAST_...json` (`src/docuflow/infrastructure/bus.py`)
- **Atomic writes**: always write to `TEMP_*` then rename — never write directly
- **HMAC signing**: messages use `json.dumps(data, sort_keys=True)` before signing — unsorted keys cause cross-node signature mismatches
- Cluster coordination: background loops in `P2POrchestrator`, gated by `is_leader` check inside symmetric loops

## Scanner/sync behavior (common regression zone)
- Folder scanning is **leader-only** — `FolderScannerSystem._discovery_loop` checks `sdk.orchestrator.is_leader`
- Scanner idempotency keys: `WorkItem.folder_name`, `TaskItem.file_path` (relative path from scan root)
- Empty production folders must transition to `PENDING_CUTS` and emit `scan.empty_folder` notification
- NS Mirror (`src/docuflow/features/folder_scanner/mirror.py`): runs on all nodes, handles local caching of network files — **network files are read-only**

## Config conventions
- `Config` in `src/docuflow/infrastructure/config.py`, env prefix `DOCUFLOW_`
- Node DB file: `f"{node_id}.db"` — each node has its own file, no shared DB
- Shared bus/snapshots paths: derived from `shared_path`, never hardcode machine paths

## Critical gotchas from knowledge gaps
- **PollingObserver**: system uses `watchdog.observers.polling.PollingObserver` (not standard `Observer`) because standard OS notifications fail over Samba/CIFS network shares
- **Async test DB**: SQLite in async tests requires `sqlite:///:memory:` + `StaticPool` — using temp files causes `database is locked` errors
- **Bulk recursive updates**: pass IDs downward, not ORM objects; use distinct `Session()` blocks in loops to avoid holding DB lock
- **Manual session scoping in admin**: `AdminSystem` uses manual `with Session(self._engine)` instead of injected session — background P2P handlers need thread-safe direct access

## Refactoring & consolidation
- See `docs/analysis/reports/CODE_CONSOLIDATION_ANALYSIS.md` for identified duplication patterns and proposed helpers
- High-impact targets: `BaseSystem` CRUD helpers, `@register_view` decorator, `styles.py` tokens, `confirm_dialog` helper
- 151+ inline Tailwind classes in views — use shared constants

## Testing conventions
- `pytest.ini` sets `pythonpath = ["src"]` — tests import from `docuflow` directly, not the installed package
- Tests enforce named constants (no magic values): see `tests/unit/test_code_quality.py`
- Public/provider methods require docstrings
- Add tests under `tests/unit` or integration area before implementing new features
