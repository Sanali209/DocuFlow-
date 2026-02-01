# Roadmap: GNC Editor & Visualization Module

This roadmap outlines the development plan for the GNC (Rexroth/Hans Laser 801) visualization and editing module. Following the user's requirements, the implementation is divided into two distinct stages: a standalone application (Stage 1) followed by deep system integration (Stage 2).

## Project Overview

**Goal:** Provide an interface for operators/technologists to verify geometry and edit technological parameters (P-codes) of .GNC files without manual text editing.

**Stack:**
- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** Svelte 5 + Canvas API
- **Deployment:** One-Folder Distributable (PyInstaller)
- **Data Format:** JSON (Intermediate representation)

---

## Current Status (Ready Items)

The following infrastructure is already in place and will be leveraged:
- [x] **Backend Framework:** FastAPI application structure (`backend/main.py`).
- [x] **Frontend Framework:** Svelte 5 + Vite setup (`frontend/`).
- [x] **Database:** SQLite + SQLAlchemy models (`backend/models.py`).
- [x] **File Handling:** Basic file upload mechanisms (`/upload` endpoint).
- [x] **Routing:** Client-side view switching in `App.svelte` and `Sidebar.svelte`.
- [ ] **OCR Module:** *REMOVED* (Paradigm shift to local file handling without OCR).

---

## Phase 1: Foundation (Weeks 1-2)
**Objective:** Build the core infrastructure for the Standalone GNC Editor.

### 1.1 One-Folder Architecture
- [ ] **Build System:** Configure PyInstaller pipeline to bundle Backend + Frontend into a single `.exe`.
- [ ] **Startup Logic:** Implement `FR-10` (DB Connection Check & Config Dialog).
- [ ] **Shared DB:** Configure SQLAlchemy to use WAL mode for `Z:\DocuFlow\data.db`.

### 1.2 GNC Parsing Engine
- [ ] **Data Models:** Pydantic schemas for `Sheet`, `Contour`, `Command`.
- [ ] **Dual-Mode Parser:**
    - Detect Office vs. Machine (`_801`) formats.
    - Parse Geometry (`G00`-`G03`).
    - Extract P-Codes (`*N... P660=`).
- [ ] **Indexing:** Calculate geometric stats (Holes, Corners) during parsing.

---

## Phase 2: MVP Editor & Sync (Weeks 3-4)
**Objective:** Deliver a usable tool for Technologists to view/edit files and sync with the network.

### 2.1 Visualization & Editing
- [ ] **Canvas:** `GncCanvas.svelte` with Zoom/Pan and Y-Axis inversion.
- [ ] **Interaction:** Click-to-select contours, P-Code property editor.
- [ ] **Save:** Regenerate GNC text file with modified parameters (preserving format).

### 2.2 Local Network Integration
- [ ] **File Watcher:** Background thread scanning `Z:\Mihtav` and `Z:\Sidra`.
- [ ] **Auto-Import Strategy:**
    - **Parts Library:** Scan "Sidra" to auto-create `Part` entities. Extract GNC code and parse Registration Numbers.
    - **Orders:** Scan "Mihtav" folders to auto-create `Document` entities (Type: Order).
    - **Status Workflow:** Set initial status to `Unregistered`. Operator must manually change to `Registered` upon receiving physical paper.
    - Extract Metadata (Material, Dates).

---

## Phase 3: Production Features (Weeks 5-6)
**Objective:** Enable full shop-floor operations with roles and material tracking.

### 3.1 Role Management
- [ ] **Modes:** Implement `Admin` (Write) vs. `Operator` (Read-Only) logic.
- [ ] **Workspaces:** Assign specific users/machines to "Workspaces".

### 3.2 Warehouse & Nesting
- [ ] **Stock:** `StockItem` CRUD (Sheets/Remnants).
- [ ] **Nesting Engine:** Integrate `SVGNest` (Python port) to pack Parts onto Stock.

### 3.3 Shift Management
- [ ] **Logs:** "Shift Handover" module for operators.
- [ ] **Action Log:** Audit trail for manual edits vs. auto-sync events.

---

## Next Steps
1.  **Approve Roadmap:** Confirm this plan fits the immediate needs.
2.  **Begin Stage 1.1:** Start implementation of `backend/gnc_parser.py`.
