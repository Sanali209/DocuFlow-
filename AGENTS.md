# AGENTS.md

## Quick orientation
- **Product**: decentralized workshop orchestration over a shared folder (no central DB), per-node SQLite + file-based sync
- **Ground truth order**: code → `docs/arhitecture_2/*` → `docs/superpowers/specs/` → older docs
- **App entrypoint**: `src/docuflow/main.py`; startup orchestration: `src/docuflow/sdk.py`, `src/docuflow/application/bus/orchestrator.py`
- **Task Board v2**: unified production center with 2 tabs (Производство, Моя корзина), hierarchy Project→WorkItem→TaskGroup→TaskItem

## Repository structure
```
DocuFlow/
├── src/                        # Ground-truth source code
│   └── docuflow/
│       ├── domain/entities/     # TaskGroup, ViewState, ViewPreset added
│       ├── features/
│       │   ├── task_board/      # v2: system.py, task_group_service.py, view.py
│       │   ├── admin/           # cluster health, identity, settings
│       │   ├── folder_scanner/  # GNC scanning + NS mirror
│       │   ├── inventory/       # material stock + reservations
│       │   ├── parts/           # part library + order cart + rework
│       │   ├── production/      # pallet tracking
│       │   ├── chat/            # workshop chat + incidents
│       │   ├── reports/         # Jinja2/weasyprint PDF reports
│       │   └── analytics/       # KPI metrics
│       ├── lib/widgets/         # hierarchy_table, hierarchy_row, filter_panel, handover_form, handover_banner
│       └── infrastructure/      # batch_engine.py removed (replaced by TaskGroupService)
├── tests/                      # Strictly categorized — no loose test_*.py in root
│   ├── unit/                   # domain, features, infrastructure, lib
│   ├── integration/
│   ├── e2e/                    # Playwright
│   ├── smoke/
│   ├── ui/
│   ├── application/
│   ├── conftest.py, helpers.py
├── docs/                       # One doc = one subfolder by purpose
│   ├── superpowers/specs/      # Design specs (e.g. 2026-04-28-task-board-v2-design.md)
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

## Task Board v2 structure
- **2 tabs**: "Производство" (full hierarchy + documents), "Моя корзина" (operator tasks + handover)
- **Hierarchy**: Project→WorkItem→TaskGroup→TaskItem (state saved in `ViewState`)
- **TaskGroup**: replaces batch_group, status aggregated from TaskItems (no own status)
- **New entities**: `TaskGroup`, `ViewState`, `ViewPreset` in `src/docuflow/domain/entities/`
- **TaskGroupService**: replaces `BatchEngine` (`src/docuflow/features/task_board/task_group_service.py`)
- **New widgets**: `hierarchy_table`, `hierarchy_row`, `filter_panel`, `handover_form`, `handover_banner` in `src/docuflow/lib/widgets/`
- **Pallet tracking**: TaskItem ↔ ProductionUnit linkage, auto-calculated `qty_produced`
- **Material reservation**: soft/hard reserves via Warehouse, auto write-off on DONE

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
- **TaskGroup status**: TaskGroup has NO own status field — status is aggregated from TaskItems (IN_PROGRESS if any, DONE if all, MIXED otherwise)
- **ViewState persistence**: expansion state saved in DB per user/view — hierarchy restores on tab return
- **TaskItemStatus.SUSPENDED**: new status for long-term suspension (brigadir/operator), distinct from short-term ON_HOLD
- **Auto-calculated qty_produced**: `qty_produced = sum(TaskPart.qty) * sheets_done` — operator does NOT enter manually
- **Material reservation**: soft reserves by default on TaskGroup assignment, auto write-off on DONE with FIFO fallback
- **TaskGroupService**: replaces BatchEngine — all batch operations now go through TaskGroupService

## Refactoring & consolidation
- See `docs/analysis/reports/CODE_AUDIT_2026_PROFESSIONAL.md` for identified duplication patterns and proposed helpers
- High-impact targets: `BaseSystem` CRUD helpers, `@register_view` decorator, `styles.py` tokens, `confirm_dialog` helper
- 151+ inline Tailwind classes in views — use shared constants

## Testing conventions
- `pytest.ini` sets `pythonpath = ["src"]` — tests import from `docuflow` directly, not the installed package
- Tests enforce named constants (no magic values): see `tests/unit/test_code_quality.py`
- Public/provider methods require docstrings
- Add tests under `tests/unit` or integration area before implementing new features

## Agent coding conventions
- **All local variables MUST have explicit type annotations**, even when the type seems obvious from the right-hand side.  
  Good: `engine: Engine = await request_container.get(Engine)`  
  Bad: `engine = await request_container.get(Engine)`
- Function signatures MUST be fully annotated (arguments + return type).
- Avoid bare `Any` when a narrower type is known; use `Any` only for genuine dynamicity.
- Prefer `|` union syntax (PEP 604) over `typing.Union` / `Optional`.
