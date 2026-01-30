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
*   **FR-02: File Upload & OCR**
    *   `POST /documents/scan`: Accept multipart file upload.
    *   Integrate with `OCR Service` via HTTP POST.
    *   Parse `markdown` response to extract Document Name using regex (`doc_name_regex` setting).
*   **FR-03: GNC Parsing**
    *   Implement `GNCProcessor` class.
    *   **Input:** `.gnc` text file.
    *   **Output:** JSON object containing:
        *   `header`: `{ width, height, thickness, material }`
        *   `contours`: Array of `{ id, type, commands: [{G00, x, y}, {G02, x, y, i, j}] }`
*   **FR-04: File System Watcher**
    *   Background task running every X minutes.
    *   Scan configured paths for folders matching `Mihtav_*` or `Sidra_*` patterns.
    *   Sync file metadata (timestamps) to Database.

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
*   **NFR-05:** OCR Service failure must not crash the main backend; should return a "Processing Failed" error gracefully.

## 4. Interfaces
*   **External:** OCR Microservice (REST/HTTP).
*   **External:** Local File System (Read/Write access to Network Shares).

## 5. Technology Stack Constraints
*   **Backend:** Python 3.10+ (FastAPI).
*   **Frontend:** Node.js 20+ (Svelte 5).
*   **Database:** SQLite (Dev), PostgreSQL (Prod).
