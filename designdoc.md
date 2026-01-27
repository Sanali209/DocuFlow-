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
| `type` | String | Type of document (e.g., "Plan", "Mail", "Other") |
| `status` | String | Status (e.g., "In Progress", "Done") |
| `registration_date` | Date | Date when the document was registered |
| `content` | Text | Markdown content extracted via OCR |

**Settings Table**: Used to store dynamic configuration.
| Field | Type | Description |
| :--- | :--- | :--- |
| `key` | String | Setting Key (PK), e.g., "ocr_url" |
| `value` | String | Setting Value |

### 3.3 API Endpoints
*   `GET /documents/`: List all documents with filtering.
*   `POST /documents/`: Create a new document.
*   `POST /documents/scan`: Proxy endpoint for OCR. Accepts file upload, calls OCR service, and extracts metadata.
*   `DELETE /documents/{id}`: Delete a document.
*   `GET/PUT /settings/{key}`: Manage application settings (e.g., OCR URL).

### 3.4 Static File Serving
The backend serves the built frontend assets from `/static` in production.

## 4. Frontend Design (`/frontend`)

### 4.1 Technology Stack
*   **Framework:** Svelte 5 (Runes).
*   **Build Tool:** Vite.
*   **Libraries:** `marked` (Markdown rendering).

### 4.2 Component Architecture
*   **`App.svelte`**: Root component.
*   **`DocumentList.svelte`**: Document table/list view.
*   **`DocumentForm.svelte`**: Create/Edit form. Handles multi-file scanning, sequential OCR calls, and content appending.
*   **`DocumentView.svelte`**: Renders markdown content (including tables) for a selected document.
*   **`SettingsModal.svelte`**: Configuration interface for the OCR Service URL.

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
