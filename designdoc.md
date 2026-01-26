# DocuFlow Design Document

## 1. Overview
**DocuFlow** is a full-stack document tracking application designed to register, manage, and search for documents. It provides a modern, responsive user interface to track document metadata such as name, type, status, and registration date.

## 2. Architecture
The application follows a **Monolithic** architecture pattern where the frontend and backend are co-located in the same repository and deployed as a single unit (though they can be decoupled during development).

*   **Frontend:** Svelte 5 (Vite-based)
*   **Backend:** FastAPI (Python 3.12+)
*   **Database:** SQLite (with SQLAlchemy ORM)
*   **Deployment:** Docker (Multi-stage build)

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

### 3.3 API Endpoints
*   `GET /documents/`: List all documents with optional filtering:
    *   `name`: Partial match search.
    *   `type`: Exact match filter.
    *   `status`: Exact match filter.
*   `POST /documents/`: Create a new document.
*   `DELETE /documents/{id}`: Delete a document by ID.

### 3.4 Static File Serving
The backend is configured to serve the frontend as static files in production.
*   It mounts the `/static` directory to serve assets (JS/CSS).
*   A catch-all route (`/{full_path:path}`) serves `index.html` to support Client-Side Routing (SPA fallback).

## 4. Frontend Design (`/frontend`)

### 4.1 Technology Stack
*   **Framework:** Svelte 5 (utilizing Runes for reactivity: `$state`, `$props`).
*   **Build Tool:** Vite.
*   **HTTP Client:** Native `fetch`.

### 4.2 Component Architecture
*   **`App.svelte`**: The root component. Handles layout structure (Header, Main Container) and manages the `Modal` state.
*   **`DocumentList.svelte`**: Displays the table of documents. Manages its own state for search queries and filters.
*   **`DocumentForm.svelte`**: A form component for creating new documents. Emits events (`onDocumentCreated`, `onCancel`) to the parent.
*   **`Modal.svelte`**: A reusable generic modal wrapper with backdrop click handling and accessibility features.

### 4.3 Styling Strategy
*   **Scoped CSS**: Most styles are defined within Svelte components.
*   **Global Layout**: `App.svelte` handles the global layout reset, utilizing `100dvh` (Dynamic Viewport Height) to ensure proper rendering on mobile browsers (addressing Chrome Android address bar shifts).
*   **Responsive Design**: The UI utilizes Flexbox and Media Queries to adapt from Desktop (Table view) to Mobile (Stacked view/Cards).

## 5. Deployment

### 5.1 Docker Strategy
The project uses a **Multi-Stage Dockerfile** to optimize image size and build efficiency.
1.  **Build Stage (`node:22`)**: Installs frontend dependencies and runs `npm run build` to generate static assets.
2.  **Runtime Stage (`python:3.12-slim`)**:
    *   Installs Python dependencies (`requirements.txt`).
    *   Copies the built frontend assets from the Build Stage to the backend's `/static` directory.
    *   Runs the FastAPI server via `uvicorn`.

### 5.2 Supported Platforms
Configuration files are provided for major PaaS providers:
*   **Render**: `render.yaml` (Infrastructure as Code).
*   **Railway**: `RAILWAY.md` (Deployment guide).
*   **Koyeb**: Docker-based deployment.

## 6. Development Workflow
1.  **Frontend**: Run `npm run dev` in `/frontend`.
2.  **Backend**: Run `uvicorn backend.main:app --reload` in root.
    *   *Note*: In development, the frontend proxy setup or CORS configuration (`ALLOWED_ORIGINS`) allows cross-origin requests.
