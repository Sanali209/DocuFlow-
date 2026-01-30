# Analysis & Recommendations: Bus Factory Metalworking System

## 1. Context Overview
The application is pivoting to serve a **Bus Factory Metalworking Shop** (Laser Cutting).
**Key Challenges:**
- **Shift Work:** 24/7 operation requiring robust handover logs.
- **File Integrity:** Machine editing (suffix `_801`) destroys metadata.
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

### 3.2 Reverse Engineering Pipeline (801 Format)
**Problem:** Machine saves edited files with the `_801` suffix in a proprietary format, but **metadata is preserved** within this structure. The challenge is parsing this non-standard text/binary format to extract the data.
**Solution:**
1.  **Format Analysis:** Collect samples of `_801` files to reverse-engineer the structure (Header locations, P-code encoding).
2.  **Custom Parser:** Develop a specialized `Gnc801Parser` class:
    -   Identify Metadata blocks (Material, Thickness, Customer).
    -   Extract Geometry (G-codes may be wrapped or encoded).
3.  **Synchronization:**
    -   When `_801` file is detected, parse it using the custom parser.
    -   Update the existing System Record with the *actual* parameters used on the machine (e.g., if the operator changed P-codes).

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

### 3.5 Distributed Synchronization Strategy ("Shared Folder as Database")
**Concept:** Instead of a single monolithic database file on the network (which causes locking issues), use a **File-Based JSON Store** structure on the shared drive.
**Optimization:** "Shared Folder as Database" Pattern.

#### Data Structure (Z:\DocuFlow_DB\)
*   `/Orders/Order_{ID}.json` (Admin writes, Operators read)
*   `/Logs/{Date}/{MachineID}_Log.json` (Operators write, Admin reads)
*   `/Inventory/Stock.json` (Admin updates, Operators read)

#### Mechanism
1.  **No Locking:** Since every Order and Log entry is a separate file (or append-only log), there is no contention for a single `.db` file.
2.  **Local Caching (SQLite):**
    -   Each machine runs a local SQLite DB for high-performance UI rendering.
    -   **WAL Mode (Write-Ahead Logging):** Enable `PRAGMA journal_mode=WAL;` on the local SQLite to ensure the UI never freezes during background sync writes.
3.  **Sync Agent (Background Thread):**
    -   **Reader:** Scans `Z:\Orders\` for modified JSONs -> Upserts to Local SQLite.
    -   **Writer:** Dumps local "New Actions" to `Z:\Logs\` as immutable JSON files.

## 4. Strategic Roadmap Adjustments
1.  **Immediate:** Implement the "Reverse Engineering" logic to stop data loss on machine edits.
2.  **Short-term:** Build the Warehouse/Inventory schema.
3.  **Mid-term:** Develop the Nesting/Packing module.
