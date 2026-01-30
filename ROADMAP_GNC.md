# Roadmap: GNC Editor & Visualization Module

This roadmap outlines the development plan for the GNC (Rexroth/Hans Laser 801) visualization and editing module. Following the user's requirements, the implementation is divided into two distinct stages: a standalone application (Stage 1) followed by deep system integration (Stage 2).

## Project Overview

**Goal:** Provide an interface for operators/technologists to verify geometry and edit technological parameters (P-codes) of .GNC files without manual text editing.

**Stack:**
- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** Svelte 5 + Canvas API
- **Data Format:** JSON (Intermediate representation)

---

## Current Status (Ready Items)

The following infrastructure is already in place and will be leveraged:
- [x] **Backend Framework:** FastAPI application structure (`backend/main.py`).
- [x] **Frontend Framework:** Svelte 5 + Vite setup (`frontend/`).
- [x] **Database:** SQLite + SQLAlchemy models (`backend/models.py`).
- [x] **File Handling:** Basic file upload mechanisms (`/upload` endpoint).
- [x] **Routing:** Client-side view switching in `App.svelte` and `Sidebar.svelte`.

---

## Stage 1: Standalone GNC Editor
**Objective:** Create a functional "separate application" (module) within the existing monorepo to parse, visualize, edit, and export GNC files. This stage focuses on the core mechanics without complex database relationships.

### 1.1 Backend: GNC Parsing & Modeling (Sprint 1)
- [ ] **Data Models:** Define Pydantic models for `Sheet`, `Contour`, `Command` (Line, Arc, Move).
- [ ] **GNC Parser:** Implement `GNCProcessor` class to:
    - Parse `.GNC` text files.
    - Extract Header info (Sheet dimensions).
    - Parse motion commands (`G00`, `G01`, `G02`, `G03`) and coordinates.
    - Extract P-codes (`P660`, `P150`, etc.) associated with contours.
- [ ] **API Endpoints:**
    - `POST /gnc/parse`: Accepts `.GNC` file, returns JSON structure.
    - `POST /gnc/build`: Accepts JSON structure, returns generated `.GNC` file.

### 1.2 Frontend: Visualization Engine (Sprint 3)
- [ ] **Canvas Component:** Create `GncCanvas.svelte`.
- [ ] **Coordinate System:** Implement transformation logic (Machine Y-Up -> Screen Y-Down) with Zoom/Pan capabilities.
- [ ] **Rendering:**
    - Draw Sheet boundaries.
    - Draw Contours (Linear and Circular segments).
    - Support for `G02/G03` arc calculations (Center point from `I, J`).
- [ ] **Interactivity:**
    - Click detection to select contours.
    - Highlighting active contour.

### 1.3 Frontend: UI & Editing Logic (Sprint 4)
- [ ] **Layout:** Implement the 4-panel layout:
    - **Top:** File info & Sheet settings.
    - **Left:** Canvas View.
    - **Right:** Parameter Editor (P-codes for selected contour).
    - **Bottom:** Status bar (Mouse coords, part count).
- [ ] **State Management:** Svelte store for the parsed GNC data.
- [ ] **Editing:** Bind Input fields in Right Panel to the selected contour's data.
- [ ] **Export:** "Download GNC" button triggering the `/gnc/build` endpoint.

---

## Stage 2: System Integration
**Objective:** Integrate the GNC Editor into the main Document Tracker workflow, allowing files to be attached to Documents/Tasks and versioned.

### 2.1 Database Integration (Sprint 2)
- [ ] **Schema Updates:** Add columns/tables to associate GNC metadata with `Documents` or `Attachments`.
- [ ] **Persistence:** Save parsed JSON states to the database to avoid re-parsing on every load.

### 2.2 Workflow Integration
- [ ] **Open from Document:** Add "Edit GNC" button on Document Card attachments.
- [ ] **Version Control:** Save edited versions as new attachments or revisions of the original document.
- [ ] **Validation:** Enforce validation rules (e.g., contours must be inside the sheet) before allowing "Task Done" status.

### 2.3 Production Verification
- [ ] **Field Testing:** Validate generated GNC files on the actual machine controller.
- [ ] **Performance:** Optimize Canvas rendering for files with large numbers of contours (>1000).

### 2.4 Part & Drawings Library Integration
- [ ] **Part Registry (Drawings Library):**
    - Create `Part` entity to store individual component definitions.
    - Attributes:
        - **Factory Registration Number:** Unique serial identifier.
        - **Type/Version:** Single English letter (e.g., 'A', 'B') denoting revision.
- [ ] **Task Linkage:**
    - Update `Task` model to support One-to-Many or Many-to-Many relationships with `Parts`.
    - Interface: Allow adding/linking specific Parts (by Reg Number) to a Task.
    - Status Tracking: Monitor production status of individual linked parts within a task.

## Stage 3: Advanced Access Control & Management
**Objective:** Implement comprehensive user management, security, and enhanced search capabilities.

### 3.1 User & Workspace Management
- [ ] **Authentication:** Implement User Login/Logout (JWT based).
- [ ] **Role-Based Access Control (RBAC):**
    - Define Roles: Operator, Technologist, Admin.
    - Permissions: Limit editing/approving GNC files based on role.
- [ ] **Workspaces (Machines):**
    - Create `Workspace` entity representing physical machines/stations.
    - Assignment: Link Users to specific Workspaces (User <-> Workspace).
    - Limit visibility/tasks based on the assigned workspace.

### 3.2 Enhanced Search & Filtering
- [ ] **Full-Text Search:** Enable searching documents by content text.
- [ ] **Tag Search:** Filter document tables by multiple tags.
- [ ] **Advanced Filtering:** Combine Text + Tags + Workspace filters in the main document list.

---

## Next Steps
1.  **Approve Roadmap:** Confirm this plan fits the immediate needs.
2.  **Begin Stage 1.1:** Start implementation of `backend/gnc_parser.py`.
