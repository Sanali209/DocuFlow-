# Analysis & Recommendations: Bus Factory Metalworking System

## 1. Context Overview
The application is pivoting to serve a **Bus Factory Metalworking Shop** (Laser Cutting).
**Key Challenges:**
- **Shift Work:** 24/7 operation requiring robust handover logs.
- **File Integrity:** Machine editing (suffix `_801`) changes the file format, requiring specialized parsing to preserve metadata.
- **Material Management:** Tracking sheets, remnants, and reservations.
- **Nesting:** Automatic packing of parts onto sheets.

## 2. Architecture Analysis

### Current State
- **Stack:** FastAPI (Backend) + Svelte 5 (Frontend).
- **Deployment:** One-Folder Executable (PyInstaller) running on each machine.
- **Data:** SQLite (Local).

### Challenge: Distributed Synchronization
Browsers cannot access local network shares (SMB) directly due to security sandboxing. Since the app runs locally on each machine ("One-Folder"), we need a mechanism to sync data between the **Admin** (Technologist) and **Operators**.

### Gap Analysis
| Feature | Current State | Missing / Risk |
|---|---|---|
| **Shift Handovers** | Basic Journal | Structured "Shift End" reports, operator authentication per session. |
| **File Reverse Eng.** | None | Parsers for machine-modified files to recover/sync metadata. |
| **Nesting** | None | Algorithmic 2D packing library. |
| **Warehouse** | Basic "Material" string | Inventory tracking (Qty, Size, Reservation). |
| **Action Log** | Basic Journal | Structured Event Sourcing or Audit Log for analytics. |

## 3. Recommendations

### 3.1 Library Integration (Frontend & Backend)

#### Frontend (Svelte 5)
1.  **Visualization (GNC/Nesting):**
    -   **Recommendation:** Continue using **HTML5 Canvas API**. It is lightweight and sufficient for 2D geometry.
    -   **Alternative:** **PixiJS** if performance drops with >10k contours (complex nesting).
2.  **Data Grids (Warehouse/Logs):**
    -   **Recommendation:** **AG Grid Community** or **TanStack Table**. Need robust filtering/sorting for inventory.

#### Backend (Python)
1.  **Nesting Engine:**
    -   **Recommendation:** **SVGnest** (port to Python) or **Deepnest** (Node.js wrapper).
    -   **Native Python:** `rectpack` (simple rectangles) or custom heuristic algorithm for irregular shapes (complex).
    -   *Constraint:* Must run locally without heavy dependencies.
2.  **File Parsing:**
    -   **Recommendation:** Custom **Regex/State-Machine Parsers**.
    -   Avoid generic libraries; machine formats (Rexroth/Hans) are proprietary and specific.

### 3.2 GNC File Analysis & Parsing Strategy
**Finding:** There are two distinct file formats: "Office" (Source) and "Machine" (Suffix `_801`). The geometry is identical, but headers and macros differ.

| Feature | Office File | Machine File (`_801`) |
|---|---|---|
| **Header** | Starts with Date/Version | Starts with `%` and Program No (`P123456`) |
| **Tech Params** | `SSD[...]` macros | `*N... P660=190` (P660 is Tech ID) |
| **Commands** | `CALL P99...` | `Q99...` |
| **Separators** | `(===== CONTOUR X =====)` | Same |

**Parsing Strategy:**
1.  **Format Detection:** Check first byte. `%` = Machine Mode, else Office Mode.
2.  **Geometry:** Parse `G00`/`G01`/`G02`/`G03` (identical in both). Ignore `CALL`/`Q` for rendering.
3.  **Parameter Extraction:**
    -   **Office:** Read `SSD` tags (if needed).
    -   **Machine:** Search for `*N... P660=...` lines inside contour blocks to get the Technology ID.
4.  **Editing Logic:**
    -   User selects a Contour -> System finds corresponding `*N` line -> Updates `P660` value -> Saves file.

### 3.3 Warehouse & Reservation Architecture
**New Entities:**
-   **StockItem:** `{ material_id, thickness, width, length, quantity, location }`
-   **Reservation:** `{ task_id, stock_item_id, quantity_reserved }`
-   **Consumption:** `{ task_id, stock_item_id, quantity_used, remnants_created }`

**Logic:**
-   **Order Creation:** Check `StockItem` availability -> Create `Reservation`.
-   **Task Completion:** Convert `Reservation` -> `Consumption`.
-   **Remnants:** If sheet utilization < 80%, prompt operator to register a "Remnant" back into `StockItem`.

### 3.4 Action Log (Analytics)
**Requirement:** Track manual vs auto events.
**Implementation:**
-   **Middleware:** Catch all state-changing API calls (`POST`, `PUT`, `DELETE`).
-   **Structured Log:** Store as JSON in a separate `AuditLog` table:
    -   `{ timestamp, actor, action_type, entity_id, previous_value, new_value }`.
-   **Analytics:** Use this table to generate "Shift Reports" (e.g., "Operator X edited 5 programs").

### 3.5 Centralized Network Database Strategy
**Concept:** Utilize the Shared Network Drive (`Z:`) as the central repository for both the Database and File Attachments.
**Constraint:** "Each server must use a shared folder with the database."

#### Data Structure (Z:\DocuFlow\)
*   `/data.db` (Shared SQLite Database)
*   `/uploads/` (Shared Attachment Storage)

#### Concurrency & Performance
1.  **Direct Connection:** All clients connect directly to `sqlite:///Z:/DocuFlow/data.db`.
2.  **WAL Mode (Critical):** SQLite's Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) is **mandatory**.
    -   Allows simultaneous readers and one writer.
    -   Significantly reduces "Database Locked" errors over networks compared to the default rollback journal.
3.  **Risk Mitigation:**
    -   Ensure the network is stable (Latencies < 10ms).
    -   If concurrency > 5 users, consider migrating the backend to a true PostgreSQL server (even if hosted on the Admin PC).

## 4. Strategic Roadmap Adjustments
1.  **Immediate:** Implement the "Reverse Engineering" logic to stop data loss on machine edits.
2.  **Short-term:** Build the Warehouse/Inventory schema.
3.  **Mid-term:** Develop the Nesting/Packing module.
