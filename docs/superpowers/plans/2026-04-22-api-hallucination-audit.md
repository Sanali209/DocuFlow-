# API Hallucination Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Find and fix imports of non-existent APIs (renamed functions, missing exports, deleted classes) — hallucinations from LLM-generated code.

**Architecture:** Systematic audit across all Python imports in `src/` and `tests/`. Phase 1: baseline runtime check via test collection. Phase 2: cross-reference each import against actual file contents. Phase 3: verify all DI provider signatures match their system classes.

**Tech Stack:** pytest, ruff, mypy, direct filesystem inspection

---

## File Structure

- `tests/ui/test_full_ui_coverage.py` — broken import: `admin_view` does not exist (renamed to `admin_view_wrapper`)
- All `src/docuflow/features/*/system.py` — check `__init__` signatures for mismatched DI params
- All `src/docuflow/features/*/view.py` — check callable signatures
- `src/docuflow/infrastructure/di.py` — verify provider signatures match system `__init__` params

---

## Phase 1: Runtime Baseline (broken imports that crash test collection)

### Task 1: Fix `tests/ui/test_full_ui_coverage.py` broken import

**Files:**
- Modify: `tests/ui/test_full_ui_coverage.py:7`

- [ ] **Step 1: Read current import line**

```python
# Line 7 currently reads:
from docuflow.features.admin.view import admin_view
```

- [ ] **Step 2: Fix import to use correct symbol**

```python
# admin_view was renamed to admin_view_wrapper when AdminView class was introduced
from docuflow.features.admin.view import admin_view_wrapper as admin_view
```

- [ ] **Step 3: Verify fix — run test collection**

Run: `uv run pytest tests/ui/test_full_ui_coverage.py --collect-only`
Expected: 234 tests collected, 0 errors

---

## Phase 2: Static Import Audit (scan all imports vs actual filesystem)

### Task 2: Audit all `src/docuflow/features/*/view.py` for missing exports

**Files:**
- Modify: `tests/unit/test_api_surface.py` (create new)
- Scan: `src/docuflow/features/*/view.py`

- [ ] **Step 1: Create test that verifies every importable symbol from each view module actually exists**

```python
# tests/unit/test_api_surface.py
"""Audit: every symbol exported in __all__ or imported by tests must exist in source."""
import importlib
import inspect
from pathlib import Path

SRC = Path("src/docuflow/features")

FEATURE_MODULES = [
    "admin.view",
    "analytics.view",
    "auth.view",
    "chat.incident_view",
    "chat.view",
    "consumables.view",
    "dashboard.view",
    "docs.portal",
    "inventory.view",
    "parts.view",
    "production.view",
    "projects.view",
    "reports.view",
    "task_board.view",
    "work_items.view",
    "folder_scanner.view",
]

IMPORTED_SYMBOLS = {
    # symbols imported by tests that are NOT re-exported via __all__
    "admin.view": ["admin_view"],  # test imports admin_view but only admin_view_wrapper exists
}

def test_all_test_imports_exist_in_source():
    """Every symbol tests import must exist in the source module."""
    failures = []
    for module_path in FEATURE_MODULES:
        full_path = f"docuflow.features.{module_path}"
        try:
            mod = importlib.import_module(full_path)
        except ImportError as e:
            failures.append(f"CANNOT IMPORT {full_path}: {e}")
            continue

        # Check imports done by tests
        if module_path in IMPORTED_SYMBOLS:
            for sym in IMPORTED_SYMBOLS[module_path]:
                if not hasattr(mod, sym):
                    failures.append(f"{full_path} lacks symbol '{sym}'")
    assert not failures, "Hallucinated imports found:\n" + "\n".join(failures)
```

- [ ] **Step 2: Run the audit test**

Run: `uv run pytest tests/unit/test_api_surface.py -v`
Expected: FAIL — admin_view not found

- [ ] **Step 3: Fix imports in test file** (see Task 1 above)

- [ ] **Step 4: Re-run audit test**

Run: `uv run pytest tests/unit/test_api_surface.py -v`
Expected: PASS

---

## Phase 3: DI Provider vs System Signature Audit

### Task 3: Verify all DI providers pass correct args to system `__init__`

**Files:**
- Scan: `src/docuflow/infrastructure/di.py`
- Scan: `src/docuflow/features/*/system.py`

- [ ] **Step 1: Write signature audit test**

```python
# tests/unit/test_di_signatures.py
"""Audit: every system __init__ receives exactly what DI providers pass."""
import inspect
from docuflow.infrastructure.di import AppProvider
from docuflow.features.admin.system import AdminSystem
from docuflow.features.analytics.system import AnalyticsSystem
from docuflow.features.auth.system import AuthSystem
from docuflow.features.chat.incidents import IncidentSystem
from docuflow.features.chat.system import ChatSystem
from docuflow.features.consumables.system import ConsumableSystem
from docuflow.features.core.search import SearchSystem
from docuflow.features.folder_scanner.system import FolderScannerSystem
from docuflow.features.folder_scanner.mirror import NSMirrorService
from docuflow.features.inventory.system import InventorySystem
from docuflow.features.notifications.system import NotificationService
from docuflow.features.parts.system import PartLibrarySystem
from docuflow.features.production.system import ProductionSystem
from docuflow.features.projects.system import ProjectSystem
from docuflow.features.reports.system import ReportSystem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.view_presets.system import ViewPresetSystem
from docuflow.features.work_items.system import WorkItemSystem

SYSTEMS = [
    AdminSystem,
    AnalyticsSystem,
    AuthSystem,
    IncidentSystem,
    ChatSystem,
    ConsumableSystem,
    SearchSystem,
    FolderScannerSystem,
    NSMirrorService,
    InventorySystem,
    NotificationService,
    PartLibrarySystem,
    ProductionSystem,
    ProjectSystem,
    ReportSystem,
    TaskBoardSystem,
    ViewPresetSystem,
    WorkItemSystem,
]

def test_all_systems_have_docstrings():
    """All public system methods must have docstrings."""
    failures = []
    for sys_cls in SYSTEMS:
        for name, method in inspect.getmembers(sys_cls, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            if not inspect.getdoc(method):
                failures.append(f"{sys_cls.__name__}.{name} has no docstring")
    assert not failures, "Missing docstrings:\n" + "\n".join(failures)
```

- [ ] **Step 2: Run signature audit**

Run: `uv run pytest tests/unit/test_di_signatures.py -v`
Expected: Shows which systems are missing docstrings

- [ ] **Step 3: Inspect ProductionSystem `__init__` — mypy shows `Session | None` issues**

Read: `src/docuflow/features/production/system.py:22`

The `__init__` accepts `session: Session` but mypy reports `Item "None" of "Session | None" has no attribute "exec"` — this means either:
- (a) DI provider passes Optional[Session] but System expects non-None, OR
- (b) System should handle Optional[Session]

Check DI provider signature in `src/docuflow/infrastructure/di.py:64`:
```python
@provide(scope=Scope.REQUEST)
def get_production_system(self, config: Config, session: Session, sdk: SDK) -> ProductionSystem:
```

DI provider type is `Session` (not Optional). This means ProductionSystem has a `Session` field typed as `Session | None` — contradiction. Fix: ProductionSystem.__init__ should accept `session: Session`, not `session: Session | None`.

- [ ] **Step 4: Fix ProductionSystem if it accepts `Session | None` incorrectly**

Only fix if investigation confirms wrong type annotation.

---

## Phase 4: TypeScript-style "used before assignment" Audit (mypy)

### Task 4: Fix high-value mypy errors that indicate real bugs

**Files:**
- Scan: `src/docuflow/features/production/system.py`
- Scan: `src/docuflow/infrastructure/coordination.py`
- Scan: `src/docuflow/infrastructure/bus.py`

- [ ] **Step 1: Run full mypy, filter to errors only (no notes)**

Run: `uv run mypy src --no-error-summary 2>&1 | Select-String "error:"`
Expected: List of actual type errors

- [ ] **Step 2: Investigate each error by file — true bug vs lint noise**

Priority fixes (true bugs):
1. `coordination.py:148` — `dict` needs type args: `dict[str, Any]`
2. `coordination.py:152` — `no-any-return` on line returning dict
3. `production/system.py:39` — Session is typed `Session | None` but code assumes non-None

Low priority (style only):
- View files missing return type annotations — NiceGUI patterns, cosmetic

---

## Phase 5: Verify No Orphaned API References in Tests

### Task 5: Full test import sweep

**Files:**
- Scan: `tests/**/*.py`

- [ ] **Step 1: Run full pytest collection to catch all import errors at once**

Run: `uv run pytest tests/ --collect-only 2>&1`
Expected: 234 tests collected, 0 errors

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-22-api-hallucination-audit.md`. Two execution options:

**1. Subagent-Driven (recommended)** — dispatch fresh subagent per task, review between tasks

**2. Inline Execution** — execute tasks in this session using executing-plans

**Which approach?**
