# Task Board v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **TDD is MANDATORY** — write failing test first, watch it fail, implement minimal code, watch it pass. **Run linters after EVERY file change:** `ruff check --fix`, `ruff format`, `pyright src`.

**Goal:** Implement unified Task Board v2 with 2 tabs (Production + My Basket), TaskGroup entity, pallet tracking, Part Library order cart, and cross-system integrations.

**Architecture:** Replace `batch_group_id` (UUID string) with `TaskGroup` (DB entity). Build unified hierarchy view (Project→WorkItem→TaskGroup→TaskItem) with ViewState persistence. Add operator basket with handover. Integrate pallet tracking, material reservation, and Part Library rework nest generation.

**Tech Stack:** Python 3.12, NiceGUI 3.9, SQLModel 0.0.37, SQLAlchemy 2.0, pytest, ruff, pyright

---

## Phase 1: DB Schema — TaskGroup, ViewState, ViewPreset, SUSPENDED

**Prerequisite:** Backup existing DB or be prepared to recreate it after schema changes.

---

### Task 1.1: Add `TaskItemStatus.SUSPENDED` enum value

**Files:**
- Modify: `src/docuflow/domain/entities/production.py`
- Test: `tests/unit/domain/test_task_item_status.py` (new)

- [ ] **Step 1: Write failing test**

```python
# tests/unit/domain/test_task_item_status.py
from docuflow.domain.entities.production import TaskItemStatus


def test_suspended_status_exists():
    assert hasattr(TaskItemStatus, "SUSPENDED")
    assert TaskItemStatus.SUSPENDED == "suspended"
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
uv run pytest tests/unit/domain/test_task_item_status.py -v
```

Expected: `AttributeError: type object 'TaskItemStatus' has no attribute 'SUSPENDED'`

- [ ] **Step 3: Add SUSPENDED to enum**

In `src/docuflow/domain/entities/production.py`, add `SUSPENDED = "suspended"` to `TaskItemStatus`.

- [ ] **Step 4: Run test — expect PASS**

```bash
uv run pytest tests/unit/domain/test_task_item_status.py -v
```

- [ ] **Step 5: Run linters**

```bash
uv run ruff check --fix src/docuflow/domain/entities/production.py
uv run ruff format src/docuflow/domain/entities/production.py
uv run pyright src/docuflow/domain/entities/production.py
```

- [ ] **Step 6: Commit**

```bash
git add tests/unit/domain/test_task_item_status.py src/docuflow/domain/entities/production.py
git commit -m "feat: Add SUSPENDED to TaskItemStatus enum"
```

---

### Task 1.2: Create `TaskGroup` entity

**Files:**
- Modify: `src/docuflow/domain/entities/production.py`
- Test: `tests/unit/domain/test_task_group_entity.py` (new)

- [ ] **Step 1: Write failing test**

```python
# tests/unit/domain/test_task_group_entity.py
from docuflow.domain.entities.production import TaskGroup


def test_task_group_has_required_fields():
    tg = TaskGroup(name="Test Group", work_item_id=1, grouping_rule="manual")
    assert tg.name == "Test Group"
    assert tg.work_item_id == 1
    assert tg.grouping_rule == "manual"
    assert tg.created_by is None
```

- [ ] **Step 2: Run test — expect FAIL** (TaskGroup not defined)

```bash
uv run pytest tests/unit/domain/test_task_group_entity.py -v
```

- [ ] **Step 3: Implement TaskGroup entity**

Add to `src/docuflow/domain/entities/production.py`:

```python
class TaskGroup(BaseEntity, table=True):
    """A group of TaskItems (replaces batch_group_id)."""

    name: str | None = None
    work_item_id: int = Field(foreign_key="workitem.id", index=True)
    created_by: str | None = None
    grouping_rule: str = Field(default="manual")  # "manual" | "auto_material"

    # Relations
    work_item: WorkItem | None = Relationship(back_populates="task_groups")
    tasks: list["TaskItem"] = Relationship(back_populates="task_group")
```

Also update `WorkItem` relations:
```python
# In WorkItem class:
task_groups: list["TaskGroup"] = Relationship(back_populates="work_item")
```

- [ ] **Step 4: Run test — expect PASS**

```bash
uv run pytest tests/unit/domain/test_task_group_entity.py -v
```

- [ ] **Step 5: Run linters**

```bash
uv run ruff check --fix src/docuflow/domain/entities/production.py
uv run ruff format src/docuflow/domain/entities/production.py
uv run pyright src/docuflow/domain/entities/production.py
```

- [ ] **Step 6: Commit**

```bash
git add tests/unit/domain/test_task_group_entity.py src/docuflow/domain/entities/production.py
git commit -m "feat: Add TaskGroup entity"
```

---

### Task 1.3: Add `task_group_id` FK to `TaskItem` and `WorkerBucketEntry`

**Files:**
- Modify: `src/docuflow/domain/entities/production.py`
- Test: `tests/unit/domain/test_task_item_fk.py` (new)

- [ ] **Step 1: Write failing test**

```python
# tests/unit/domain/test_task_item_fk.py
from docuflow.domain.entities.production import TaskItem


def test_task_item_has_task_group_id():
    task = TaskItem(work_item_id=1, file_name="test.gnc")
    assert hasattr(task, "task_group_id")
    assert task.task_group_id is None
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Add FK fields**

In `TaskItem`:
```python
# Replace: batch_group_id: str | None = None
task_group_id: int | None = Field(default=None, foreign_key="taskgroup.id")
task_group: TaskGroup | None = Relationship(back_populates="tasks")
```

In `WorkerBucketEntry`:
```python
# Replace: batch_group_id: str | None = None
task_group_id: int | None = Field(default=None, foreign_key="taskgroup.id")
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/domain/entities/production.py tests/unit/domain/test_task_item_fk.py
git commit -m "feat: Add task_group_id FK to TaskItem and WorkerBucketEntry"
```

---

### Task 1.4: Create `ViewState` and `ViewPreset` entities

**Files:**
- Modify: `src/docuflow/domain/entities/production.py`
- Test: `tests/unit/domain/test_view_state_preset.py` (new)

- [ ] **Step 1: Write failing test**

```python
# tests/unit/domain/test_view_state_preset.py
from docuflow.domain.entities.production import ViewState, ViewPreset


def test_view_state_fields():
    vs = ViewState(user_id="admin", view_name="task_board", entity_type="project", entity_id="1")
    assert vs.is_expanded is True


def test_view_preset_fields():
    vp = ViewPreset(name="My Filter", user_id="admin", view_name="task_board", filters_json="{}")
    assert vp.is_default is False
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement entities**

Add to `src/docuflow/domain/entities/production.py`:

```python
class ViewState(BaseEntity, table=True):
    """Persists expansion state of hierarchy levels."""

    __table_args__ = (UniqueConstraint("user_id", "view_name", "entity_type", "entity_id"),)

    user_id: str = Field(index=True)
    view_name: str = Field(index=True)
    entity_type: str  # "project" | "workitem" | "taskgroup"
    entity_id: str
    is_expanded: bool = Field(default=True)


class ViewPreset(BaseEntity, table=True):
    """Saved filter configurations."""

    name: str = Field(index=True)
    user_id: str = Field(index=True)
    view_name: str = Field(index=True)
    filters_json: str
    is_default: bool = Field(default=False)
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/domain/entities/production.py tests/unit/domain/test_view_state_preset.py
git commit -m "feat: Add ViewState and ViewPreset entities"
```

---

### Task 1.5: Update `VALID_TASK_TRANSITIONS` for SUSPENDED

**Files:**
- Modify: `src/docuflow/features/task_board/system.py`
- Test: `tests/unit/features/test_task_transitions.py` (new)

- [ ] **Step 1: Write failing test**

```python
# tests/unit/features/test_task_transitions.py
from docuflow.domain.entities.production import TaskItemStatus
from docuflow.features.task_board.system import TaskBoardSystem


def test_suspended_transitions():
    tbs = TaskBoardSystem.__new__(TaskBoardSystem)
    allowed = tbs.VALID_TASK_TRANSITIONS[TaskItemStatus.IN_PROGRESS]
    assert TaskItemStatus.SUSPENDED in allowed
    assert TaskItemStatus.DONE in tbs.VALID_TASK_TRANSITIONS[TaskItemStatus.SUSPENDED]
```

- [ ] **Step 2: Run test — expect FAIL** (SUSPENDED not in transitions)

- [ ] **Step 3: Update transitions**

In `src/docuflow/features/task_board/system.py`:
```python
VALID_TASK_TRANSITIONS = {
    TaskItemStatus.PLANNED: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
    TaskItemStatus.IN_PROGRESS: [
        TaskItemStatus.ON_HOLD,
        TaskItemStatus.SUSPENDED,
        TaskItemStatus.DONE,
        TaskItemStatus.BLOCKED,
        TaskItemStatus.CANCELLED,
    ],
    TaskItemStatus.ON_HOLD: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
    TaskItemStatus.SUSPENDED: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.DONE, TaskItemStatus.CANCELLED],
    TaskItemStatus.BLOCKED: [TaskItemStatus.IN_PROGRESS, TaskItemStatus.CANCELLED],
    TaskItemStatus.DONE: [],
    TaskItemStatus.CANCELLED: [],
}
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/features/task_board/system.py tests/unit/features/test_task_transitions.py
git commit -m "feat: Add SUSPENDED to valid task transitions"
```

---

## Phase 2: TaskGroupService (replacement for BatchEngine)

---

### Task 2.1: Create `TaskGroupService` with `auto_group_by_material`

**Files:**
- Create: `src/docuflow/features/task_board/task_group_service.py`
- Delete: `src/docuflow/features/task_board/batch_engine.py` (after migration)
- Test: `tests/unit/features/test_task_group_service.py` (new)

- [ ] **Step 1: Write failing test**

```python
# tests/unit/features/test_task_group_service.py
import pytest
from sqlmodel import Session, SQLModel, create_engine
from docuflow.domain.entities.production import (
    MaterialType, TaskGroup, TaskItem, TaskItemStatus, WorkItem,
)
from docuflow.features.task_board.task_group_service import TaskGroupService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_auto_group_by_material(session):
    # Setup
    mat = MaterialType(code="ST37-2", thickness=4.0)
    session.add(mat)
    session.flush()

    wi = WorkItem(project_id=1, folder_name="test")
    session.add(wi)
    session.flush()

    t1 = TaskItem(work_item_id=wi.id, file_name="a.gnc", mat_type_id=mat.id, thickness=4.0, status=TaskItemStatus.PLANNED)
    t2 = TaskItem(work_item_id=wi.id, file_name="b.gnc", mat_type_id=mat.id, thickness=4.0, status=TaskItemStatus.PLANNED)
    session.add_all([t1, t2])
    session.commit()

    service = TaskGroupService(session)
    groups = service.auto_group_by_material(wi.id)

    assert len(groups) == 1
    assert groups[0].name == "ST37-2 4.0mm"
    assert len(groups[0].tasks) == 2
```

- [ ] **Step 2: Run test — expect FAIL** (TaskGroupService not found)

- [ ] **Step 3: Implement TaskGroupService**

```python
# src/docuflow/features/task_board/task_group_service.py
from sqlmodel import Session, select

from docuflow.domain.entities.production import TaskGroup, TaskItem


class TaskGroupService:
    """Manages TaskGroup lifecycle — replaces BatchEngine."""

    def __init__(self, session: Session):
        self.session = session

    def auto_group_by_material(self, work_item_id: int) -> list[TaskGroup]:
        """Group tasks by material+thickness."""
        tasks = list(self.session.exec(
            select(TaskItem).where(TaskItem.work_item_id == work_item_id)
        ).all())

        # Group by (mat_type_id, thickness)
        groups: dict[tuple[int | None, float | None], list[TaskItem]] = {}
        for task in tasks:
            key = (task.mat_type_id, task.thickness)
            groups.setdefault(key, []).append(task)

        result = []
        for (mat_id, thickness), task_list in groups.items():
            name = self._generate_group_name(mat_id, thickness)
            tg = TaskGroup(
                name=name,
                work_item_id=work_item_id,
                grouping_rule="auto_material",
            )
            self.session.add(tg)
            self.session.flush()

            for task in task_list:
                task.task_group_id = tg.id
                self.session.add(task)

            result.append(tg)

        self.session.commit()
        return result

    def _generate_group_name(self, mat_type_id: int | None, thickness: float | None) -> str:
        if mat_type_id:
            mat = self.session.get(MaterialType, mat_type_id)
            if mat:
                return f"{mat.code} {thickness or '-'}mm"
        return f"Unknown {thickness or '-'}mm"

    def create_manual_group(self, task_ids: list[int], name: str | None = None) -> TaskGroup:
        """Create manual group from task IDs."""
        tasks = []
        for tid in task_ids:
            task = self.session.get(TaskItem, tid)
            if task:
                tasks.append(task)

        if not tasks:
            raise ValueError("No tasks found")

        tg = TaskGroup(
            name=name or f"Group ({len(tasks)} tasks)",
            work_item_id=tasks[0].work_item_id,
            grouping_rule="manual",
        )
        self.session.add(tg)
        self.session.flush()

        for task in tasks:
            task.task_group_id = tg.id
            self.session.add(task)

        self.session.commit()
        return tg

    def get_group_status(self, group: TaskGroup) -> str:
        """Aggregate status from tasks."""
        statuses = {t.status for t in group.tasks}
        if TaskItemStatus.IN_PROGRESS in statuses:
            return "in_progress"
        if statuses == {TaskItemStatus.DONE}:
            return "done"
        if statuses == {TaskItemStatus.PLANNED}:
            return "planned"
        return "mixed"
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/features/task_board/task_group_service.py tests/unit/features/test_task_group_service.py
git commit -m "feat: Add TaskGroupService with auto_group_by_material"
```

---

### Task 2.2: Add remaining `TaskGroupService` methods

**Files:**
- Modify: `src/docuflow/features/task_board/task_group_service.py`
- Test: `tests/unit/features/test_task_group_service.py`

- [ ] **Step 1: Write failing tests for move_task_to_group, split_group, merge_groups**

```python
def test_move_task_to_group(session):
    # Setup 2 groups with 1 task each
    ...
    service = TaskGroupService(session)
    service.move_task_to_group(task1.id, group2.id)
    assert task1.task_group_id == group2.id


def test_split_group(session):
    ...
    new_group = service.split_group(group.id, [task1.id])
    assert task1.task_group_id == new_group.id
    assert task2.task_group_id == group.id
```

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement methods**

```python
def move_task_to_group(self, task_id: int, group_id: int) -> None:
    task = self.session.get(TaskItem, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    group = self.session.get(TaskGroup, group_id)
    if not group:
        raise ValueError(f"Group {group_id} not found")
    task.task_group_id = group_id
    self.session.add(task)
    self.session.commit()


def split_group(self, group_id: int, task_ids_to_separate: list[int]) -> TaskGroup:
    original = self.session.get(TaskGroup, group_id)
    if not original:
        raise ValueError(f"Group {group_id} not found")

    new_group = TaskGroup(
        name=f"{original.name} (split)",
        work_item_id=original.work_item_id,
        grouping_rule="manual",
    )
    self.session.add(new_group)
    self.session.flush()

    for tid in task_ids_to_separate:
        task = self.session.get(TaskItem, tid)
        if task and task.task_group_id == group_id:
            task.task_group_id = new_group.id
            self.session.add(task)

    self.session.commit()
    return new_group


def merge_groups(self, group_ids: list[int]) -> TaskGroup:
    groups = []
    for gid in group_ids:
        g = self.session.get(TaskGroup, gid)
        if g:
            groups.append(g)

    if len(groups) < 2:
        raise ValueError("Need at least 2 groups to merge")

    merged = TaskGroup(
        name=f"Merged ({len(groups)} groups)",
        work_item_id=groups[0].work_item_id,
        grouping_rule="manual",
    )
    self.session.add(merged)
    self.session.flush()

    for g in groups:
        for task in g.tasks:
            task.task_group_id = merged.id
            self.session.add(task)

    self.session.commit()
    return merged
```

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/features/task_board/task_group_service.py tests/unit/features/test_task_group_service.py
git commit -m "feat: Add TaskGroupService move/split/merge methods"
```

---

## Phase 3: Backend — Updated TaskBoardSystem

---

### Task 3.1: Add `suspend_task` method to TaskBoardSystem

**Files:**
- Modify: `src/docuflow/features/task_board/system.py`
- Test: `tests/unit/features/test_task_board_system.py`

- [ ] **Step 1: Write failing test**

```python
def test_suspend_task(session, db_engine):
    from docuflow.features.task_board.system import TaskBoardSystem
    from docuflow.infrastructure.config import Config

    config = Config(node_id="test")
    system = TaskBoardSystem(config=config, db_engine=db_engine, session=session)

    task = TaskItem(work_item_id=1, file_name="test.gnc", status=TaskItemStatus.IN_PROGRESS)
    session.add(task)
    session.commit()
    session.refresh(task)

    result = system.suspend_task(task.id)
    assert result.status == TaskItemStatus.SUSPENDED
```

- [ ] **Step 2: Run test — expect FAIL** (suspend_task not found)

- [ ] **Step 3: Implement**

```python
def suspend_task(self, task_id: int) -> TaskItem:
    with self.get_db_session() as session:
        task_item = self._validate_transition(task_id, TaskItemStatus.SUSPENDED, session)
        task_item.status = TaskItemStatus.SUSPENDED
        self._audit_task_event(
            task_item, WorkLogType.STATUS_CHANGE, "Task suspended", session=session
        )
        session.add(task_item)
        self._sync(session)
        session.refresh(task_item)
        return task_item
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/features/task_board/system.py tests/unit/features/test_task_board_system.py
git commit -m "feat: Add suspend_task to TaskBoardSystem"
```

---

### Task 3.2: Auto-calculate `qty_produced` in `complete_task`

**Files:**
- Modify: `src/docuflow/features/task_board/system.py`
- Test: `tests/unit/features/test_task_board_system.py`

- [ ] **Step 1: Write failing test**

```python
def test_complete_task_auto_qty_produced(session, db_engine):
    config = Config(node_id="test")
    system = TaskBoardSystem(config=config, db_engine=db_engine, session=session)

    task = TaskItem(work_item_id=1, file_name="test.gnc", sheet_qty=8, status=TaskItemStatus.IN_PROGRESS, started_at=datetime.datetime.now())
    session.add(task)
    session.commit()
    session.refresh(task)

    # Add TaskParts: 2 parts per sheet
    from docuflow.domain.entities.production import TaskPart
    p1 = TaskPart(task_item_id=task.id, part_sku="BASE-A", qty=2)
    session.add(p1)
    session.commit()

    result = system.complete_task(task.id, sheets_done=4, qty_produced=0)  # qty_produced ignored
    assert result.qty_produced == 8  # 2 parts * 4 sheets
```

- [ ] **Step 2: Run test — expect FAIL** (qty_produced not auto-calculated)

- [ ] **Step 3: Modify complete_task**

In `complete_task`, before setting `task_item.qty_produced`:

```python
# Auto-calculate qty_produced from TaskParts
if task_item.parts:
    parts_per_sheet = sum(p.qty for p in task_item.parts)
    auto_qty = parts_per_sheet * sheets_done
else:
    auto_qty = sheets_done

# If caller provided qty_produced, validate it matches auto (within tolerance)
# Otherwise use auto
if qty_produced > 0 and abs(qty_produced - auto_qty) > (auto_qty * 0.1):
    logger.warning(f"qty_produced mismatch: provided={qty_produced}, auto={auto_qty}")

task_item.qty_produced = auto_qty if qty_produced == 0 else qty_produced
```

Also update signature: `def complete_task(self, task_id: int, sheets_done: int, qty_produced: int = 0, ...)`

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/features/task_board/system.py tests/unit/features/test_task_board_system.py
git commit -m "feat: Auto-calculate qty_produced from TaskParts in complete_task"
```

---

### Task 3.3: Update `complete_task` to handle pallet selection

**Files:**
- Modify: `src/docuflow/features/task_board/system.py`
- Test: `tests/unit/features/test_task_board_system.py`

- [ ] **Step 1: Write failing test**

```python
def test_complete_task_creates_pallet(session, db_engine):
    config = Config(node_id="test")
    system = TaskBoardSystem(config=config, db_engine=db_engine, session=session)

    task = TaskItem(work_item_id=1, file_name="test.gnc", sheet_qty=8, status=TaskItemStatus.IN_PROGRESS, started_at=datetime.datetime.now())
    session.add(task)
    session.commit()
    session.refresh(task)

    result = system.complete_task(task.id, sheets_done=8, qty_produced=0, create_pallet=True)
    assert result.status == TaskItemStatus.DONE

    # Verify pallet was created
    pallets = session.exec(select(ProductionUnit).where(ProductionUnit.task_item_id == task.id)).all()
    assert len(pallets) == 1
    assert pallets[0].qty_produced == 8
```

- [ ] **Step 2: Run test — expect FAIL** (or verify existing behavior)

- [ ] **Step 3: Verify/Update existing pallet creation logic**

Existing `complete_task` already has `create_pallet` parameter and calls `production_system.register_finished_pallet`. Ensure it uses `auto_qty` when `qty_produced=0`.

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/features/task_board/system.py tests/unit/features/test_task_board_system.py
git commit -m "feat: complete_task auto-creates pallet with auto qty_produced"
```

---

### Task 3.4: Add `find_pallets_by_task` / `find_task_by_pallet` methods

**Files:**
- Modify: `src/docuflow/features/task_board/system.py` or `src/docuflow/features/production/system.py`
- Test: `tests/unit/features/test_pallet_search.py` (new)

- [ ] **Step 1: Write failing test**

```python
def test_find_pallets_by_task(session):
    from docuflow.features.production.system import ProductionSystem

    task = TaskItem(work_item_id=1, file_name="test.gnc")
    session.add(task)
    session.commit()
    session.refresh(task)

    pallet = ProductionUnit(label_id="TEST-001", task_item_id=task.id, qty_produced=10)
    session.add(pallet)
    session.commit()

    # Method to implement
    from docuflow.features.task_board.system import TaskBoardSystem
    tbs = TaskBoardSystem.__new__(TaskBoardSystem)
    pallets = tbs.find_pallets_by_task(task.id, session)
    assert len(pallets) == 1
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement search methods**

Add to `TaskBoardSystem`:

```python
def find_pallets_by_task(self, task_id: int, session: Session | None = None) -> list[ProductionUnit]:
    session = session or self.get_db_session()
    return list(session.exec(select(ProductionUnit).where(ProductionUnit.task_item_id == task_id)).all())

def find_pallets_by_work_item(self, work_item_id: int, session: Session | None = None) -> list[ProductionUnit]:
    session = session or self.get_db_session()
    return list(session.exec(
        select(ProductionUnit).join(TaskItem).where(TaskItem.work_item_id == work_item_id)
    ).all())

def find_task_by_pallet_label(self, label_id: str, session: Session | None = None) -> TaskItem | None:
    session = session or self.get_db_session()
    pallet = session.exec(select(ProductionUnit).where(ProductionUnit.label_id == label_id)).first()
    return pallet.task_item if pallet else None
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/features/task_board/system.py tests/unit/features/test_pallet_search.py
git commit -m "feat: Add pallet search by task/work_item and reverse lookup"
```

---

## Phase 4: UI — Task Board "Производство" Tab (Hierarchy)

---

### Task 4.1: Create `HierarchyTable` widget

**Files:**
- Create: `src/docuflow/lib/widgets/hierarchy_table.py`
- Test: `tests/ui/test_hierarchy_table.py` (new, smoke test)

- [ ] **Step 1: Write failing test**

```python
def test_hierarchy_table_renders():
    from docuflow.lib.widgets.hierarchy_table import HierarchyTable
    # Smoke test: can instantiate
    ht = HierarchyTable(user_id="admin", view_name="task_board", system_scope=None)
    assert ht.user_id == "admin"
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement skeleton**

```python
# src/docuflow/lib/widgets/hierarchy_table.py
from typing import Any

from nicegui import ui

from docuflow.lib.base_widget import BaseDocuWidget


class HierarchyTable(BaseDocuWidget):
    """Tree-like hierarchy table for Project→WorkItem→TaskGroup→TaskItem."""

    def __init__(self, user_id: str, view_name: str, system_scope: Any):
        super().__init__(system_scope)
        self.user_id = user_id
        self.view_name = view_name

    def render(self) -> None:
        """Render the hierarchy."""
        with ui.column().classes("w-full gap-1"):
            ui.label("Hierarchy placeholder").classes("text-slate-500")
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Run linters**

- [ ] **Step 6: Commit**

```bash
git add src/docuflow/lib/widgets/hierarchy_table.py tests/ui/test_hierarchy_table.py
git commit -m "feat: Add HierarchyTable skeleton widget"
```

---

### Task 4.2: Create `HierarchyRow` widget (two-line row)

**Files:**
- Create: `src/docuflow/lib/widgets/hierarchy_row.py`
- Test: `tests/ui/test_hierarchy_row.py` (new)

- [ ] **Step 1–6: Implement with TDD** (similar pattern — write test, implement skeleton, linters, commit)

Key features:
- Two-line layout: title+badges on line 1, metadata+actions on line 2
- Expand/collapse toggle
- Action buttons per entity type

---

### Task 4.3: Implement `render_project_row`, `render_workitem_row`, `render_taskgroup_row`, `render_taskitem_row`

Continue with TDD for each row type. Each task: write test → implement → linters → commit.

---

### Task 4.4: Integrate `HierarchyTable` into Task Board view

**Files:**
- Modify: `src/docuflow/features/task_board/view.py`
- Delete/deprecate: `src/docuflow/features/projects/view.py`, `src/docuflow/features/work_items/view.py`

---

## Phase 5: UI — "Моя корзина" Tab + Handover

---

### Task 5.1: Create `HandoverForm` widget

**Files:**
- Create: `src/docuflow/lib/widgets/handover_form.py`
- Test: `tests/ui/test_handover_form.py`

---

### Task 5.2: Create `HandoverBanner` widget

**Files:**
- Create: `src/docuflow/lib/widgets/handover_banner.py`
- Test: `tests/ui/test_handover_banner.py`

---

### Task 5.3: Integrate basket + handover into Task Board view

**Files:**
- Modify: `src/docuflow/features/task_board/view.py`

---

## Phase 6: Pallet Tracking UI + Material Reservation

---

### Task 6.1: Show pallet info in TaskItemRow (DONE status)

**Files:**
- Modify: `src/docuflow/lib/widgets/hierarchy_row.py`

---

### Task 6.2: Add reservation modal for TaskGroup

**Files:**
- Create: `src/docuflow/lib/widgets/reservation_modal.py`
- Modify: `src/docuflow/features/inventory/view.py` (add "РЕЗЕРВЫ" tab)

---

## Phase 7: Part Library — Order Cart + Rework Nest

---

### Task 7.1: Create `OrderCart` data structure

**Files:**
- Create: `src/docuflow/features/parts/order_cart.py`
- Test: `tests/unit/features/test_order_cart.py`

---

### Task 7.2: Create `OrderCartPanel` widget

**Files:**
- Create: `src/docuflow/lib/widgets/order_cart_panel.py`
- Test: `tests/ui/test_order_cart_panel.py`

---

### Task 7.3: Create `ReworkGenerator`

**Files:**
- Create: `src/docuflow/features/parts/rework_generator.py`
- Test: `tests/unit/features/test_rework_generator.py`

---

## Phase 8: Integrations (Chat, Incidents, Analytics, Reports, Omnisearch)

---

### Task 8.1: Add ChatMessageType.HANDOVER

**Files:**
- Modify: `src/docuflow/domain/entities/production.py`
- Modify: `src/docuflow/features/chat/view.py`

---

### Task 8.2: Update Analytics metrics

**Files:**
- Modify: `src/docuflow/features/analytics/system.py`
- Modify: `src/docuflow/features/analytics/view.py`

---

### Task 8.3: Add new ReportDataBlocks

**Files:**
- Modify: `src/docuflow/features/reports/system.py`

---

### Task 8.4: Update Omnisearch

**Files:**
- Modify: `src/docuflow/features/core/search.py`

---

## Phase 9: Cleanup & Final Integration

---

### Task 9.1: Remove `batch_engine.py`

**Files:**
- Delete: `src/docuflow/features/task_board/batch_engine.py`
- Update all imports

---

### Task 9.2: Run full test suite

```bash
uv run pytest tests/ -v
```

---

### Task 9.3: Run full linter suite

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pyright src
```

---

### Task 9.4: Final commit

```bash
git commit -m "feat: Complete Task Board v2 implementation"
```

---

## Linter Rules (MANDATORY after EVERY file change)

```bash
# After modifying ANY .py file:
uv run ruff check --fix <file>
uv run ruff format <file>
uv run pyright src
```

If pyright reports errors — fix them before proceeding. No `# type: ignore` without explicit approval.

---

## Self-Review Checklist

- [ ] Every new function has a test
- [ ] Every test was watched failing first
- [ ] `ruff check --fix` passes on all modified files
- [ ] `ruff format` applied to all modified files
- [ ] `pyright src` passes (no new errors)
- [ ] All 23 acceptance criteria from spec have corresponding tasks
- [ ] No placeholders (TBD, TODO, "implement later") in plan or code
