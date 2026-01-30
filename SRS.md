# Software Requirements Specification (SRS)
**Project:** DocuFlow
**Version:** 1.0

## 1. Introduction
This SRS document provides the specific technical requirements for the DocuFlow system, including the Backend API, Frontend Interface, and GNC Processing Module. It serves as the definitive guide for developers.

## 2. Functional Requirements

### 2.1 Backend API (FastAPI)
*   **FR-01: Document CRUD**
    *   `POST /documents/`: Create document with metadata.
    *   `GET /documents/`: Support filtering by `type`, `status`, `tags`, `date_range`.
    *   `PUT /documents/{id}`: Update metadata.
*   **FR-02: File Upload**
    *   `POST /upload`: Accept multipart file upload.
    *   Save files to `static/uploads/`.
*   **FR-03: GNC Parsing**
    *   Implement `GNCProcessor` class with **Dual-Mode** parsing.
    *   **Detection:** If file starts with `%` -> Machine Mode (`_801`), else Office Mode.
    *   **Contours:** Split by delimiter `(===== CONTOUR X =====)`.
    *   **P-Codes:** Extract `P660={Value}` from lines starting with `*N`.
    *   **Output:** JSON object containing contours and their P-code technology IDs.
*   **FR-04: File System Watcher**
    *   Background task running every X minutes.
    *   Scan configured paths for folders matching `Mihtav_*` or `Sidra_*` patterns.
    *   Sync file metadata (timestamps) to Database.
*   **FR-05: 801 Format Decoding**
    *   Parse lines starting with `*N`.
    *   Extract Technology ID (`P660`) and Speed Factors (`P150`, `P151`).
    *   Ignore `Q` command differences.
*   **FR-06: Warehouse & Nesting**
    *   `StockItems` table: Material, Thickness, Qty, Reserved.
    *   `NestingEngine`: Python module (using `rectpack` or similar) to pack parts on sheets.

### 2.2 Frontend (Svelte 5)
*   **FR-05: GNC Canvas**
    *   Component: `GncCanvas.svelte`.
    *   Must implement Coordinate Transformation: `Screen_Y = Canvas_Height - (Machine_Y * Scale)`.
    *   Support Pan (translate) and Zoom (scale) interactions.
*   **FR-06: Interactive Editing**
    *   Clicking a rendered path must emit a `select` event with the Contour ID.
    *   Right-panel inputs must bind two-way to the selected Contour's `P-code` properties.

### 2.3 Data & Storage
*   **FR-07: Database Schema**
    *   `Documents` table: Stores core metadata.
    *   `Parts` table: `registration_number` (String), `version` (Char).
    *   `Workspaces` table: `name`, `machine_id`.
*   **FR-08: File Storage**
    *   Physical files stored in `static/uploads/{uuid}_{filename}`.
    *   GNC files tracked via `Attachments` table or dedicated `GNCPrograms` table.

## 3. Non-Functional Requirements

### 3.1 Performance
*   **NFR-01:** API response time for `/documents` list < 200ms (with < 1000 items).
*   **NFR-02:** Canvas rendering 60FPS for standard complexity parts (< 5000 segments).

### 3.2 Security
*   **NFR-03:** Input sanitization for all file uploads (prevent path traversal).
*   **NFR-04:** JWT Authentication for all write operations (Planned for Stage 3).

### 3.3 Reliability
*   **NFR-05:** Application must be portable (One-Folder) and not require pre-installed Python.
*   **NFR-06:** Database Persistence: System must connect to a central SQLite file on a Network Share (`Z:\`).
*   **NFR-07:** Concurrency: WAL Mode must be enabled to support multiple readers.

## 4. Interfaces
*   **External:** Shared Network Drive (SMB/Z:) hosting the `data.db` and `uploads/`.

## 5. Technology Stack Constraints
*   **Backend:** Python 3.10+ (FastAPI).
*   **Frontend:** Node.js 20+ (Svelte 5).
*   **Database:** SQLite (Dev), PostgreSQL (Prod).
