# DocuFlow Design Document

## 1. Overview
**DocuFlow** is a full-stack document tracking application designed to register, manage, and search for documents. It provides a modern, responsive user interface to track document metadata such as name, type, status, and registration date, and includes AI-powered OCR capabilities for extracting content from images and PDFs.

## 2. Architecture
The application follows a **Monolithic** architecture pattern for the core app (Frontend + Backend) with a **Microservice** extension for the OCR capabilities.

*   **Frontend:** Svelte 5 (Vite-based)
*   **Backend:** FastAPI (Python 3.12+)
*   **OCR Service:** FastAPI + Docling (Dockerized Microservice)
*   **Database:** SQLite (with SQLAlchemy ORM)
*   **Deployment:** Docker (Multi-stage build for App, Separate Container for OCR)

## 3. Backend Design (`/backend`)

### 3.1 Technology Stack
*   **Framework:** FastAPI
*   **ORM:** SQLAlchemy
*   **Schema Validation:** Pydantic
*   **Server:** Uvicorn

### 3.2 Data Model
The core entity is the **Document**.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Primary Key (Auto-increment) |
| `name` | String | Document Name (Indexed) |
| `description` | Text | Brief description of the document |
| `type` | String | Type of document (e.g., "Plan", "Mail", "Other") |
| `status` | String | Status (e.g., "In Progress", "Done") |
| `registration_date` | Date | Date when the document was registered |
| `done_date` | Date | Date when status changed to Done |
| `author` | String | Person responsible for the document |
| `content` | Text | Markdown content extracted via OCR |

**Related Entities:**
*   **Task**: Embedded tasks linked to a document (`status`, `assignee`, `name`).
*   **Attachment**: Files linked to a Document or Journal Entry.
*   **JournalEntry**: Notes/Activity logs, can be linked to a specific Document.
*   **Tag**: Many-to-Many relationship with Documents for categorization.
*   **FilterPreset**: Saved user configurations for list filtering.

**Settings Table**: Used to store dynamic configuration.
| Field | Type | Description |
| :--- | :--- | :--- |
| `key` | String | Setting Key (PK), e.g., "ocr_url", "doc_name_regex" |
| `value` | String | Setting Value |

### 3.3 API Endpoints
*   `GET /documents/`: List all documents with filtering (search, type, status, tag, date range, assignee) and sorting.
*   `POST /documents/`: Create a new document.
*   `POST /documents/scan`: Proxy endpoint for OCR. Accepts file upload, calls OCR service, extracts metadata, and saves attachment.
*   `DELETE /documents/{id}`: Delete a document.
*   `GET/POST/DELETE /documents/{id}/tasks`: Manage document tasks.
*   `PUT /tasks/{id}`: Update task status and assignee.
*   `GET /tags`: List all available tags.
*   `GET/POST/DELETE /filter-presets`: Manage saved filters. Presets store all filter configurations including task types.
*   `GET/PUT /settings/{key}`: Manage application settings.

### 3.4 Static File Serving
The backend serves the built frontend assets from `/static` in production and user uploads from `/static/uploads`.

## 4. Frontend Design (`/frontend`)

### 4.1 Technology Stack
*   **Framework:** Svelte 5 (Runes).
*   **Build Tool:** Vite.
*   **Libraries:** `marked` (Markdown rendering).

### 4.2 Mobile Optimizations
*   **Responsive Sidebar**: Displays only icons on mobile devices (< 768px). Hover expansion is disabled on mobile to prevent accidental expansion.
*   **Compact Layouts**: Reduced padding and spacing on cards, tasks, and notes for mobile screens (< 640px).
*   **Touch-Friendly**: Larger touch targets and optimized spacing for mobile interaction.
*   **Adaptive Typography**: Font sizes scale down appropriately for mobile devices.

### 4.3 Component Architecture
*   **`App.svelte`**: Root component.
*   **`DocumentList.svelte`**: Main view. Renders documents as Cards. Features integrated filtering bar (Search, Type, Status, Tag, Date Range, Presets). Supports filtering by task types and assignee.
*   **`DocumentForm.svelte`**: Create/Edit form. Handles multi-file scanning, sequential OCR calls, tagging (`TagInput`), and content appending.
*   **`DocumentTasks.svelte`**: Embedded component within the Document Card for managing tasks inline. Supports filtering by assignee when provided via props.
*   **`DocumentView.svelte`**: Read-only detailed view rendering markdown content and attachments.
*   **`JournalEntryModal.svelte`**: Popup to add notes linked to a specific document.
*   **`ImagePreviewModal.svelte`**: Gallery modal for viewing attached images.
*   **`TagInput.svelte`**: Reusable component for tag selection with autocomplete based on existing tags.
*   **`SettingsModal.svelte`**: Configuration interface for OCR Service URL and Regex.
*   **`Sidebar.svelte`**: Navigation sidebar with icon-only display on mobile devices (< 768px). Expands on hover for desktop.
*   **`FilterModal.svelte`**: Advanced filter interface supporting task type filtering, assignee filtering, and preset management.

## 5. OCR Service (`/ocr_service`)

### 5.1 Overview
A dedicated microservice wrapping the IBM Docling library. It exposes a REST API to convert documents to Markdown.

### 5.2 Technology Stack
*   **Base Image:** `python:3.12-slim` (Debian-based).
*   **OCR Engine:** Docling (with EasyOCR, RapidOCR, Tesseract, and TableFormer).
*   **Server:** FastAPI.

### 5.3 Deployment
*   Designed for **Hugging Face Spaces**.
*   Runs as a non-root user (`user` 1000) for security and permission compatibility.
*   Pre-downloads models during build to optimize runtime startup.
*   Configured to support both PDF and Image inputs with advanced table structure analysis.

## 6. Deployment Strategy

### 6.1 Main Application
Uses a Multi-Stage Dockerfile to build the Svelte frontend and bundle it with the Python backend.

### 6.2 OCR Service
Deployed separately (e.g., HF Spaces) due to high resource requirements (PyTorch, OCR models) and to decouple heavy dependencies from the main CRUD app.

## 7. Development Workflow
1.  **OCR Service**: `docker run -p 7860:7860 docling-ocr`
2.  **Backend**: `uvicorn backend.main:app --reload`
3.  **Frontend**: `npm run dev`
