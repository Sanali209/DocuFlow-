# Session Summary: 2026-04-28 — Task Board v2 Compliance + Bug Fixes

## Session Goal
Analyze and close gaps between current implementation and `docs/superpowers/specs/2026-04-28-task-board-v2-design.md`.

## Phase 1: Bug Fixes & Architecture Alignment

### 1.1 BucketPanel — batch_group_id → task_group_id Migration
**Problem:** BucketPanel grouped entries by legacy `batch_group_id` string instead of using the new `TaskGroup` entity via `task_group_id`.
**Solution:**
- Modified `_group_by_batch` in `src/docuflow/lib/widgets/bucket_panel.py` to group by `task.task_group_id`
- Removed unused `**kwargs` from `BucketPanel.__init__`
- Added migration script: `scripts/ops/migrate_add_batch_group_id.py`
- **Test:** `tests/unit/test_bucket_panel_grouping.py` — verifies grouping by TaskGroup

### 1.2 Hierarchy Pallet Display
**Problem:** TaskGroupRow only showed pallet count, not individual pallet labels with quantities.
**Solution:**
- Extracted `_build_taskgroup_line2` helper in `src/docuflow/lib/widgets/hierarchy_table.py`
- Now renders: `📦 26-04-LASER_1-0015 (47 шт)` for each DONE task's pallet
- **Test:** `tests/unit/test_hierarchy_table_pallets.py`

### 1.3 TaskItemModal Enhancement
**Problem:** TaskItemModal had a single generic `on_action` callback, no status-specific buttons, no history.
**Solution:**
- Added optional callbacks: `on_start`, `on_pause`, `on_complete`, `on_incident`
- Renders contextual action buttons based on `task.status`:
  - `PLANNED` → [▶ Старт]
  - `IN_PROGRESS` → [⏸ Пауза] [✓ Завершить]
  - Any → [⚠️ Инцидент]
- Maintained backward compatibility with legacy `on_action`
- **Test:** `tests/ui/test_task_item_modal_enhanced.py`

### 1.4 Runtime Bug Fixes
- **DetachedInstanceError** in hierarchy toggle: captured `project_id` before session closure
- **ValueError** "Invalid transition IN_PROGRESS→IN_PROGRESS": added idempotency guard in `_validate_transition`
- **OperationalError** `no such column: workerbucketentry.batch_group_id`: ran DB migration

**Commit:** `60c2065` — `fix(task-board): align BucketPanel grouping with TaskGroup entity + enhance modals`

---

## Phase 2: Integration Features

### 2.1 Omnisearch — ProductionUnit + Part SKU
**Status:** ✅ Already implemented
- `SearchSystem.search()` in `src/docuflow/features/core/search.py` already searches:
  - WorkItems by `folder_name` / `sidra_number`
  - PartLibrary by `sku` / `name`
  - ProductionUnit by `label_id`
- No changes needed.

### 2.2 Chat — HANDOVER Type + Deeplink
**Status:** ✅ Already implemented
- `ChatMessageType.HANDOVER` exists in `domain/entities/production.py`
- `view.py` parses `#<task_id>` patterns and renders clickable links to `/task_board?task_id={id}`
- No changes needed.

### 2.3 Incidents — Project/WorkItem Filter + Deeplink
**Problem:** IncidentView had no filtering by project or work_item; IncidentLog lacked `project_id`.
**Solution:**
- Added `project_id` column to `IncidentLog` entity (`domain/entities/production.py`)
- Added `active_project_filter` and `active_work_item_filter` to `IncidentView`
- Added `_matches_filters()` helper combining group + project + work_item filters
- Applied filtering in `refresh_active_feed()` loop
- Deeplink `#<task_id>` already existed in incident cards
- Added migration script: `scripts/ops/migrate_add_incident_project_id.py`
- **Test:** `tests/ui/test_incident_view_filters.py`

**Commit:** `44dcc11` — `feat(incidents): add project/work_item filters to IncidentView`

### 2.4 Warehouse — "РЕЗЕРВЫ" Tab
**Status:** ✅ Already implemented
- `src/docuflow/features/inventory/view.py` has `reservations_tab` with full reservation listing
- Shows: material, quantity, work item link, cancel button
- No changes needed.

---

## Phase 3: Analytics & Reports

### 3.1 Analytics Metrics
**Status:** ✅ Already implemented
- `analytics/system.py` computes:
  - `total_task_groups`
  - `groups_by_status` (planned/in_progress/done/mixed)
  - `node_utilization` (active/queued/done per node)
  - `pallet_by_project`
- No changes needed.

### 3.2 Report Data Blocks
**Status:** ✅ Already implemented
- `reports/system.py` registers:
  - `task_group_summary`
  - `material_reservation_status`
  - `pallet_by_project`
- No changes needed.

---

## Quality Gates

### Linting Stack (all passing)
| Tool | Command | Status |
|------|---------|--------|
| Ruff | `uv run ruff check src/` | ✅ 0 errors |
| Pyright | `uv run pyright src` | ✅ 0 errors |
| import-linter | `uv run lint-imports` | ✅ 3 kept, 0 broken |
| Vulture | `uv run vulture src/ --min-confidence 80` | ✅ 0 dead code |

### Tests
- **Unit tests:** 261 passed
- **UI tests:** 7 passed (entity_modals, task_item_modal_enhanced, incident_view_filters)
- **Total:** 268 passed

### Pre-commit Hooks
All commits passed:
1. `ruff check --fix`
2. `ruff format`
3. `pyright`
4. `import-linter`
5. `vulture`

---

## Files Created
```
scripts/ops/migrate_add_batch_group_id.py       # DB migration: add batch_group_id
scripts/ops/migrate_add_incident_project_id.py  # DB migration: add project_id to incidentlog
tests/unit/test_bucket_panel_grouping.py        # Unit test: TaskGroup grouping
tests/unit/test_hierarchy_table_pallets.py      # Unit test: pallet display in hierarchy
tests/ui/test_task_item_modal_enhanced.py       # UI test: TaskItemModal callbacks
tests/ui/test_incident_view_filters.py          # UI test: incident filtering
```

## Files Modified
```
src/docuflow/domain/entities/production.py      # +project_id to IncidentLog
src/docuflow/features/chat/incident_view.py     # +filters, +_matches_filters
src/docuflow/features/task_board/system.py      # +idempotency guard
src/docuflow/lib/widgets/bucket_panel.py        # task_group_id grouping, -kwargs
src/docuflow/lib/widgets/entity_modals.py       # +action callbacks
src/docuflow/lib/widgets/hierarchy_table.py     # +_build_taskgroup_line2, +pallet display
```

## Commits
1. `60c2065` — fix(task-board): align BucketPanel grouping with TaskGroup entity + enhance modals
2. `44dcc11` — feat(incidents): add project/work_item filters to IncidentView

## Specification Compliance
| Section | Status | Notes |
|---------|--------|-------|
| 3.1 Hierarchy (Project→WorkItem→TaskGroup→TaskItem) | ✅ Complete |
| 3.2 Two-line rows | ✅ Complete |
| 3.3 Expandable cards | ✅ Complete |
| 3.4 Project management | ✅ Complete |
| 3.5 WorkItem management | ✅ Complete |
| 3.6 TaskGroup management | ✅ Complete |
| 3.7 Filters & presets | ✅ Complete |
| 4 DB Schema (TaskGroup, ViewState, ViewPreset) | ✅ Complete |
| 5 Omnisearch | ✅ Complete |
| 6 TaskGroupService | ✅ Complete |
| 7 Data migration | ✅ Complete |
| 8 API / Backend | ✅ Complete |
| 9 UI Components | ✅ Complete |
| 10 Acceptance criteria (mandatory) | ✅ Complete |
| 13 Pallet tracking & material reservation | ✅ Complete |
| 15 Part Library / Warehouse / Pallets integration | ✅ Complete |
| 16 Chat / Incidents / Analytics / Reports | ✅ Complete |
| 18-20 Modals / Nest preview / Rework | ✅ Complete |
| 21 Final acceptance criteria | ✅ Complete |

**Overall: ~100% of mandatory specification items are implemented and tested.**
