# Task Board v2 — Next Steps Implementation Plan

## Task A: nest_preview.py — SVG Nesting Visualization

**Goal:** Create widget that renders SVG nest preview showing part contours positioned on sheet.

**Files:**
- Create: `src/docuflow/lib/widgets/nest_preview.py`
- Test: `tests/ui/test_nest_preview.py`
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py` (show preview in TaskItem modal/row)

**Approach:**
- Load part SVG contours from `PartLibrary.svg_preview_path`
- Position them on sheet rectangle using bbox data
- Generate inline SVG string
- Render with `ui.html()` (same pattern as PartLibrary view)

## Task B: Entity Modals (5 modals)

**Goal:** Full view/edit modals for each hierarchy entity.

**Files:**
- Create: `src/docuflow/lib/widgets/entity_modals.py` (all 5 modals)
- Test: `tests/ui/test_entity_modals.py`
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py` (add "Просмотр" buttons)

**Modals:**
1. **ProjectModal** — name, description, deadline, status, list of WorkItems
2. **WorkItemModal** — folder_name, project, sidra_number, status, file list, TaskGroups
3. **TaskGroupModal** — name, tasks list with progress, assign to node button
4. **TaskItemModal** — full info + nest preview + history + action buttons
5. **PalletModal** — label_id, qty, task link, location, split/merge/ship buttons

## Task C: GNC File Generation for Rework Nests

**Goal:** Generate actual GNC files with part contours for rework orders.

**Files:**
- Modify: `src/docuflow/features/parts/rework_generator.py`
- Test: `tests/unit/features/test_rework_generator.py` (expand)

**Approach:**
- Load part contours from `PartLibrary` (stored as SVG path data or GNC commands)
- Position parts on sheet in grid layout
- Generate GNC file with: SHEET header, MATERIAL, PART NAME blocks, contours
- Save to `rework/<sidra_name>/Sheet_*.GNC`

## Task D: Drag-and-Drop

**Goal:** Allow moving WorkItems between Projects and TaskGroups to nodes.

**Files:**
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py`
- Modify: `src/docuflow/features/task_board/system.py`

**Approach:**
- Use NiceGUI `ui.select` dropdowns as MVP (true HTML5 DnD is complex in NiceGUI)
- "Переместить в проект" dropdown on WorkItem row
- "Назначить на узел" dropdown on TaskGroup row

## Task E: Real-Time Sync Between Tabs

**Goal:** Auto-refresh tabs when data changes.

**Files:**
- Modify: `src/docuflow/features/task_board/view.py`
- Modify: `src/docuflow/lib/widgets/hierarchy_table.py`
- Modify: `src/docuflow/lib/widgets/bucket_panel.py`

**Approach:**
- Add `ui.timer(5.0, self.render.refresh)` to TaskBoardView
- Register timer with layout for cleanup
- Only refresh if data changed (compare hash/timestamp)

---

## Execution Order

1. Tasks A, B, C — parallel (independent)
2. Task D — after B (uses modal patterns)
3. Task E — last (affects all tabs)
