# DocuFlow Design Document

## 1. Overview

### 1.1 Project Vision
**DocuFlow** is a comprehensive document management system designed to streamline document tracking, organization, and retrieval in modern organizations. It combines traditional document management capabilities with cutting-edge AI-powered OCR technology to provide an intelligent, user-friendly solution.

### 1.2 Core Purpose
The application serves as a centralized platform for:
- **Document Registration & Tracking**: Complete lifecycle management of documents
- **Intelligent Content Extraction**: AI-powered text and table extraction from images/PDFs
- **Task Management**: Embedded task tracking linked to documents
- **Search & Discovery**: Advanced filtering and full-text search capabilities
- **Collaboration**: Notes, tags, and assignee management

### 1.3 Target Users
- Small to medium-sized teams managing document-heavy workflows
- Organizations requiring document compliance and tracking
- Teams needing OCR capabilities for digitizing paper documents
- Project managers tracking document-related tasks and deliverables

## 2. Architecture

### 2.1 Architectural Pattern
The application follows a **Hybrid Monolithic-Microservices** architecture:
- **Monolithic Core**: Frontend and Backend are tightly integrated for simplicity
- **Microservice Extension**: OCR service is decoupled for scalability and resource isolation

### 2.2 Technology Stack

#### Frontend Layer
*   **Framework:** Svelte 5 with Runes API
*   **Build Tool:** Vite (Fast HMR, optimized builds)
*   **Rendering:** `marked` library for Markdown rendering
*   **Styling:** Modern CSS with responsive design
*   **State Management:** Svelte's reactive stores

#### Backend Layer
*   **Framework:** FastAPI (Python 3.12+)
*   **ORM:** SQLAlchemy 2.0+
*   **Schema Validation:** Pydantic v2
*   **Server:** Uvicorn (ASGI server)
*   **Database:** SQLite (default), PostgreSQL-ready
*   **HTTP Client:** httpx for async requests

#### OCR Microservice
*   **Base Image:** `python:3.12-slim`
*   **OCR Engine:** IBM Docling
*   **Supporting Libraries:** EasyOCR, RapidOCR, Tesseract, TableFormer
*   **Model Management:** Pre-downloaded during build
*   **Deployment:** Dockerized, Hugging Face Spaces compatible

### 2.3 System Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│              Client Browser                      │
│         (Desktop / Mobile / Tablet)             │
└────────────────┬────────────────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────────────────┐
│           Reverse Proxy (Nginx)                 │
│         SSL Termination / Load Balancing        │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         Frontend (Svelte 5 + Vite)             │
│  ┌──────────────────────────────────────────┐  │
│  │  Components: DocumentList, Form, Tasks   │  │
│  │  State Management: Svelte Stores         │  │
│  │  Router: Client-side navigation          │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │ REST API (JSON)
┌────────────────▼────────────────────────────────┐
│          Backend (FastAPI)                      │
│  ┌──────────────────────────────────────────┐  │
│  │  API Endpoints: /documents, /tasks, etc │  │
│  │  Business Logic: CRUD operations         │  │
│  │  Authentication: (Future) JWT tokens     │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│  ┌──────────────▼───────────────────────────┐  │
│  │       SQLAlchemy ORM                     │  │
│  │  Models: Document, Task, Tag, etc       │  │
│  └──────────────┬───────────────────────────┘  │
└─────────────────┼───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│       SQLite Database (or PostgreSQL)          │
│  Tables: documents, tasks, tags, journal,      │
│          attachments, filter_presets           │
└─────────────────────────────────────────────────┘

     Backend also connects to OCR Service:
     
┌────────────────┐  HTTP POST    ┌────────────────┐
│ Backend FastAPI├──────────────►│  OCR Service   │
│ /documents/scan│  /convert     │  (Docling)     │
└────────────────┘  multipart    └────────────────┘
```

### 2.4 Design Principles

1. **Separation of Concerns**: Frontend, Backend, and OCR are clearly separated
2. **API-First**: RESTful API design with OpenAPI documentation
3. **Scalability**: OCR service can scale independently
4. **Mobile-First**: Responsive design prioritizing mobile experience
5. **Progressive Enhancement**: Core features work without OCR service
6. **Data Integrity**: Database constraints and validation at multiple layers
7. **Performance**: Efficient queries, indexing, and caching strategies

## 3. Backend Design (`/backend`)

### 3.1 Technology Stack
*   **Framework:** FastAPI
*   **ORM:** SQLAlchemy
*   **Schema Validation:** Pydantic
*   **Server:** Uvicorn

### 3.2 Data Model

#### 3.2.1 Core Entity: Document

The **Document** is the central entity in the system.

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `name` | String(255) | NOT NULL, Indexed | Document name/title |
| `description` | Text | Nullable | Brief description |
| `type` | String(50) | NOT NULL | Document type (Plan, Mail, Order, etc.) |
| `status` | String(50) | NOT NULL | Current status (In Progress, Done, etc.) |
| `registration_date` | Date | NOT NULL, Default=today | Registration timestamp |
| `done_date` | Date | Nullable | Completion date |
| `author` | String(100) | Nullable | Person responsible |
| `content` | Text | Nullable | Markdown content from OCR |

**Indexes:**
- `idx_document_name`: ON name (for fast search)
- `idx_document_type`: ON type (for filtering)
- `idx_document_status`: ON status (for filtering)

#### 3.2.2 Related Entities

**Task Entity**
- Represents tasks/action items linked to documents
- Enables tracking of work items within document context

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key | Unique task identifier |
| `document_id` | Integer | Foreign Key → documents.id, ON DELETE CASCADE | Parent document |
| `name` | String(255) | NOT NULL | Task description |
| `status` | String(50) | NOT NULL, Default='Planned' | Task status (Planned/Pending/Done) |
| `assignee` | String(100) | Nullable | Person assigned to task |
| `order_index` | Integer | Default=0 | Display order |

**Attachment Entity**
- Stores file references for documents and journal entries

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key | Unique attachment identifier |
| `filename` | String(255) | NOT NULL | Original filename |
| `filepath` | String(500) | NOT NULL | Server storage path |
| `document_id` | Integer | Foreign Key → documents.id, Nullable | Linked document |
| `journal_entry_id` | Integer | Foreign Key → journal_entries.id, Nullable | Linked journal |
| `uploaded_at` | DateTime | NOT NULL, Default=now | Upload timestamp |

**JournalEntry Entity**
- Activity log and notes system

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key | Entry identifier |
| `document_id` | Integer | Foreign Key → documents.id, ON DELETE CASCADE | Linked document |
| `entry_text` | Text | NOT NULL | Note content |
| `created_at` | DateTime | NOT NULL, Default=now | Creation timestamp |

**Tag Entity & Association**
- Many-to-Many relationship for categorization

```python
# Association Table
document_tags = Table(
    'document_tags',
    Column('document_id', ForeignKey('documents.id')),
    Column('tag_id', ForeignKey('tags.id')),
    PrimaryKey('document_id', 'tag_id')
)

# Tag Table
class Tag:
    id: Integer (Primary Key)
    name: String(100) (Unique, NOT NULL)
```

**FilterPreset Entity**
- Saved filter configurations for quick access

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key | Preset identifier |
| `name` | String(100) | NOT NULL | Preset name |
| `filters` | JSON/Text | NOT NULL | Serialized filter config |
| `created_at` | DateTime | NOT NULL | Creation timestamp |

**Settings Entity**
- Key-value store for application configuration

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `key` | String(100) | Primary Key | Setting identifier |
| `value` | Text | NOT NULL | Setting value |

**Common Settings:**
- `ocr_url`: OCR service endpoint URL
- `doc_name_regex`: Regex pattern for auto-extraction

#### 3.2.3 Entity Relationship Diagram

```
┌──────────────┐
│   Document   │
│──────────────│
│ id (PK)      │◄──────┐
│ name         │       │
│ description  │       │ 1
│ type         │       │
│ status       │       │
│ reg_date     │       │
│ done_date    │       │
│ author       │       │
│ content      │       │
└──────┬───────┘       │
       │               │
       │ 1             │
       │               │
       │ *             │ *
       ▼               │
┌──────────────┐       │
│     Task     │       │
│──────────────│       │
│ id (PK)      │       │
│ document_id  │───────┘
│ name         │
│ status       │
│ assignee     │
│ order_index  │
└──────────────┘

┌──────────────┐       ┌──────────────┐
│   Document   │       │     Tag      │
│──────────────│ *   * │──────────────│
│ id (PK)      │◄─────►│ id (PK)      │
│ ...          │       │ name         │
└──────────────┘       └──────────────┘
      ▲                (via document_tags)
      │
      │ 1
      │
      │ *
┌──────────────┐
│JournalEntry  │
│──────────────│
│ id (PK)      │
│ document_id  │
│ entry_text   │
│ created_at   │
└──────────────┘

┌──────────────┐
│  Attachment  │
│──────────────│
│ id (PK)      │
│ filename     │
│ filepath     │
│ document_id  │───┐
│ journal_id   │   │ * (nullable)
│ uploaded_at  │   │
└──────────────┘   │
                   ▼ 1
            ┌──────────────┐
            │   Document   │
            └──────────────┘
```

### 3.3 API Endpoints

#### 3.3.1 Document Management

**List Documents**
```
GET /documents/
Query Parameters:
  - search: string (search across name, description, content)
  - type: string (filter by document type)
  - status: string (filter by status)
  - tag: string (filter by tag name)
  - assignee: string (filter by task assignee)
  - reg_date_from: date (registration date range start)
  - reg_date_to: date (registration date range end)
  - done_date_from: date (completion date range start)
  - done_date_to: date (completion date range end)
  - task_statuses: comma-separated (filter docs with specific task statuses)
  - sort: string (default: "-registration_date")
  
Response: 200 OK
  [
    {
      "id": 1,
      "name": "Project Plan Q1",
      "description": "Quarterly planning document",
      "type": "Plan",
      "status": "In Progress",
      "registration_date": "2024-01-15",
      "done_date": null,
      "author": "John Doe",
      "content": "# Project Overview...",
      "tasks": [...],
      "tags": [...],
      "journal_entries": [...],
      "attachments": [...]
    }
  ]
```

**Create Document**
```
POST /documents/
Request Body:
  {
    "name": "string",
    "description": "string (optional)",
    "type": "string",
    "status": "string",
    "registration_date": "date (optional, defaults to today)",
    "done_date": "date (optional)",
    "author": "string (optional)",
    "content": "string (optional)"
  }

Response: 201 Created
  { "id": 1, "name": "...", ... }
```

**Update Document**
```
PUT /documents/{id}
Request Body: (same as POST, all fields optional)
Response: 200 OK
```

**Delete Document**
```
DELETE /documents/{id}
Response: 204 No Content
```

**Scan Document (OCR)**
```
POST /documents/scan
Content-Type: multipart/form-data
Form Data:
  - files: File[] (multiple files supported)
  - document_id: integer (optional, for appending to existing doc)

Process:
  1. Uploads files to OCR service
  2. Extracts text/tables via Docling
  3. Auto-extracts document name via regex
  4. Saves files as attachments
  5. Returns extracted content

Response: 200 OK
  {
    "extracted_text": "markdown content",
    "extracted_name": "auto-detected name",
    "attachments": [...]
  }
```

#### 3.3.2 Task Management

**List Document Tasks**
```
GET /documents/{document_id}/tasks
Response: 200 OK
  [
    {
      "id": 1,
      "name": "Review document",
      "status": "Pending",
      "assignee": "Jane Doe",
      "order_index": 0
    }
  ]
```

**Create Task**
```
POST /documents/{document_id}/tasks
Request Body:
  {
    "name": "string",
    "status": "Planned|Pending|Done",
    "assignee": "string (optional)"
  }

Response: 201 Created
```

**Update Task**
```
PUT /tasks/{task_id}
Request Body:
  {
    "name": "string (optional)",
    "status": "string (optional)",
    "assignee": "string (optional)"
  }

Response: 200 OK
```

**Delete Task**
```
DELETE /documents/{document_id}/tasks/{task_id}
Response: 204 No Content
```

#### 3.3.3 Tag Management

**List All Tags**
```
GET /tags
Response: 200 OK
  [
    { "id": 1, "name": "urgent" },
    { "id": 2, "name": "financial" }
  ]
```

**Create Tag** (implicit via document tagging)

#### 3.3.4 Journal Entries

**Create Journal Entry**
```
POST /documents/{document_id}/journal
Request Body:
  {
    "entry_text": "string"
  }

Response: 201 Created
```

#### 3.3.5 Attachments

**Upload Attachment**
```
POST /documents/{document_id}/attachments
Content-Type: multipart/form-data
Form Data:
  - file: File

Response: 201 Created
  {
    "id": 1,
    "filename": "document.pdf",
    "filepath": "/uploads/abc123.pdf"
  }
```

**Download Attachment**
```
GET /uploads/{filepath}
Response: File stream
```

#### 3.3.6 Filter Presets

**List Presets**
```
GET /filter-presets
Response: 200 OK
  [
    {
      "id": 1,
      "name": "Urgent Tasks",
      "filters": {
        "status": "In Progress",
        "task_statuses": ["Pending", "Planned"]
      }
    }
  ]
```

**Create Preset**
```
POST /filter-presets
Request Body:
  {
    "name": "string",
    "filters": { ... }
  }

Response: 201 Created
```

**Delete Preset**
```
DELETE /filter-presets/{id}
Response: 204 No Content
```

#### 3.3.7 Settings

**Get Setting**
```
GET /settings/{key}
Response: 200 OK
  {
    "key": "ocr_url",
    "value": "http://localhost:7860"
  }
```

**Update Setting**
```
PUT /settings/{key}
Request Body:
  {
    "value": "string"
  }

Response: 200 OK
```

#### 3.3.8 API Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`

### 3.4 Static File Serving
The backend serves the built frontend assets from `/static` in production and user uploads from `/static/uploads`.

**Static File Configuration:**
```python
# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Serve frontend (production mode)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

**Upload Directory Structure:**
```
uploads/
├── documents/
│   ├── abc123_filename.pdf
│   └── def456_image.jpg
└── temp/
    └── processing/
```

### 3.5 Security Considerations

#### 3.5.1 Input Validation
- **Pydantic Schemas**: All API inputs validated via Pydantic models
- **SQL Injection**: Protected by SQLAlchemy ORM
- **File Upload Validation**: Filename sanitization, size limits
- **XSS Prevention**: Content-Type headers, markdown sanitization

#### 3.5.2 File Upload Security
```python
# Sanitize filenames
safe_filename = secure_filename(file.filename)

# Validate file types
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}

# Size limits
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
```

#### 3.5.3 Future Security Enhancements
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- HTTPS enforcement
- CORS configuration for production
- Database encryption at rest

### 3.6 Performance Optimization

#### 3.6.1 Database Optimization
- **Indexes**: On frequently queried columns (name, type, status)
- **Eager Loading**: Relationships loaded efficiently
- **Connection Pooling**: SQLAlchemy pool configuration
- **Query Optimization**: Use of select_related/join strategies

#### 3.6.2 API Performance
- **Async Operations**: FastAPI's async capabilities for I/O operations
- **Response Compression**: Gzip middleware
- **Pagination**: (Future) Limit/offset for large result sets
- **Caching**: (Future) Redis for frequently accessed data

## 4. Frontend Design (`/frontend`)

### 4.1 Technology Stack
*   **Framework:** Svelte 5 with Runes API (modern reactive paradigm)
*   **Build Tool:** Vite (Fast dev server, optimized production builds)
*   **Libraries:** 
    - `marked`: Markdown to HTML conversion
    - Native fetch API for HTTP requests
*   **Styling:** Modern CSS with CSS Variables for theming
*   **State Management:** Svelte's reactive stores and runes

### 4.2 Mobile Optimizations

#### 4.2.1 Responsive Design Breakpoints
```css
/* Mobile: <= 640px */
@media (max-width: 640px) {
  /* Compact layouts, stacked elements */
}

/* Tablet: 641px - 768px */
@media (min-width: 641px) and (max-width: 768px) {
  /* Hybrid layouts */
}

/* Desktop: > 768px */
@media (min-width: 769px) {
  /* Full-featured layouts */
}
```

#### 4.2.2 Mobile-Specific Features
*   **Icon-Only Sidebar**: Navigation shows only icons on mobile (<= 768px)
*   **Compact Cards**: Reduced padding and spacing for mobile screens (<= 640px)
*   **Touch-Friendly Targets**: Minimum 44x44px touch targets
*   **Adaptive Typography**: Font sizes scale appropriately
*   **Gesture Support**: Swipe gestures for navigation (future enhancement)
*   **Responsive Tables**: Horizontal scroll for markdown tables on small screens

### 4.3 Component Architecture

#### 4.3.1 Core Components

**`App.svelte`** - Root Component
- Application shell
- Global state initialization
- Route handling (future: proper router)
- Error boundary (future)

**`Sidebar.svelte`** - Navigation Component
- Icon-based navigation
- Hover expansion on desktop
- Touch-friendly on mobile
- Active route highlighting

**`DocumentList.svelte`** - Main Document View
- Card-based document display
- Integrated filter bar
- Real-time search
- Sorting controls
- Pagination (future)

**`DocumentCard.svelte`** - Individual Document Display
- Status badge
- Tags display
- Inline tasks
- Inline journal entries
- Attachment gallery
- Actions menu (edit, delete)

**`DocumentForm.svelte`** - Create/Edit Form
- Multi-step form flow
- File upload with preview
- Multi-file OCR scanning
- Tag input with autocomplete
- Form validation
- Markdown editor (future enhancement)

**`DocumentView.svelte`** - Read-Only Detail View
- Markdown rendering
- Table formatting
- Image preview
- Print-friendly layout

#### 4.3.2 Task Management Components

**`DocumentTasks.svelte`** - Embedded Task List
- Inline task display within cards
- Status toggle (Planned → Pending → Done)
- Assignee dropdown
- Task creation form
- Drag-and-drop reordering (future)
- Filter by assignee (when prop provided)

**`TaskItem.svelte`** - Individual Task Component
- Status badge with color coding
- Assignee display
- Inline edit mode
- Delete confirmation

#### 4.3.3 Supporting Components

**`TagInput.svelte`** - Tag Selection Component
- Autocomplete from existing tags
- Multi-select capability
- Tag creation on-the-fly
- Visual tag chips
- Keyboard navigation

**`JournalEntryModal.svelte`** - Notes Dialog
- Simple textarea input
- Timestamp display
- Link to parent document
- Rich text editor (future)

**`ImagePreviewModal.svelte`** - Gallery Viewer
- Full-screen image preview
- Navigation between images
- Zoom controls (future)
- Download button

**`SettingsModal.svelte`** - Configuration Dialog
- OCR service URL input
- Document name regex configuration
- Form validation
- Test connection button (future)

**`FilterModal.svelte`** - Advanced Filters Dialog
- Multi-criteria filter form
- Date range pickers
- Tag multi-select
- Task status checkboxes
- Assignee dropdown
- Preset management (save/load/delete)
- Clear all filters button

#### 4.3.4 Component Communication

**State Management Pattern:**
```javascript
// Svelte stores for global state
import { writable } from 'svelte/store';

export const documents = writable([]);
export const tags = writable([]);
export const filterPresets = writable([]);
export const settings = writable({});

// Component uses stores
let $documents; // Auto-subscription
```

**Props Down, Events Up:**
```svelte
<!-- Parent passes data down -->
<DocumentCard 
  document={doc} 
  on:edit={handleEdit}
  on:delete={handleDelete} 
/>

<!-- Child emits events up -->
<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
  
  function handleAction() {
    dispatch('edit', { id: document.id });
  }
</script>
```

### 4.4 Routing Strategy

**Current**: Single-page application with component visibility toggling
**Future**: Implement proper client-side routing (e.g., svelte-routing)

```
/                    → DocumentList (Home)
/documents/new       → DocumentForm (Create)
/documents/:id       → DocumentView (Read-only)
/documents/:id/edit  → DocumentForm (Edit)
/settings           → SettingsModal
```

### 4.5 API Integration

**HTTP Client Configuration:**
```javascript
const API_BASE = window.location.origin; // Production
// const API_BASE = 'http://localhost:8000'; // Development

async function fetchDocuments(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${API_BASE}/documents/?${params}`);
  return await response.json();
}
```

**Error Handling:**
```javascript
try {
  const data = await apiCall();
  return { success: true, data };
} catch (error) {
  console.error('API Error:', error);
  return { success: false, error: error.message };
}
```

### 4.6 Build and Deployment

**Development Build:**
```bash
npm run dev  # Vite dev server on port 5173
```

**Production Build:**
```bash
npm run build  # Outputs to frontend/dist/
```

**Build Configuration** (`vite.config.js`):
```javascript
export default defineConfig({
  base: './',  // Relative paths for production
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,  // Disable for production
    minify: 'terser',
  }
})
```

### 4.7 User Experience Patterns

#### 4.7.1 Loading States
- Skeleton screens for initial load
- Spinner for async operations
- Progressive rendering

#### 4.7.2 Error Handling
- Toast notifications for user feedback
- Inline validation errors
- Retry mechanisms for failed requests

#### 4.7.3 Accessibility
- Semantic HTML elements
- ARIA labels for screen readers
- Keyboard navigation support
- Focus management in modals
- Color contrast compliance (WCAG AA)

## 5. OCR Service (`/ocr_service`)

### 5.1 Overview
A dedicated microservice wrapping the IBM Docling library. It exposes a REST API to convert documents (images and PDFs) to structured Markdown with table recognition.

**Key Responsibilities:**
- Document format detection (PDF vs Image)
- Text extraction using multiple OCR engines
- Table structure recognition and preservation
- Markdown formatting with semantic structure
- Model caching for performance

### 5.2 Technology Stack

**Core Libraries:**
*   **Docling**: IBM's document understanding framework
*   **EasyOCR**: Neural network-based OCR engine
*   **RapidOCR**: Fast OCR for quick text extraction
*   **Tesseract**: Traditional OCR engine (fallback)
*   **TableFormer**: Deep learning model for table structure recognition
*   **PyTorch**: ML framework for neural models
*   **FastAPI**: REST API server
*   **Pillow**: Image processing

**Docker Configuration:**
*   **Base Image:** `python:3.12-slim` (Debian-based)
*   **Non-root User:** Runs as user ID 1000 for security
*   **Model Pre-download**: Models cached during build phase
*   **Port**: 7860 (Hugging Face Spaces standard)

### 5.3 API Endpoints

#### Convert Document to Markdown
```
POST /convert
Content-Type: multipart/form-data

Form Data:
  - file: File (PDF or Image: PNG, JPEG, JPG)

Response: 200 OK
{
  "markdown": "# Extracted Content\n\n| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |",
  "metadata": {
    "page_count": 3,
    "has_tables": true,
    "processing_time_ms": 2450
  }
}

Error Response: 400/500
{
  "detail": "Error message"
}
```

#### Health Check
```
GET /health
Response: 200 OK
{
  "status": "healthy",
  "models_loaded": true,
  "version": "1.0.0"
}
```

### 5.4 Document Processing Pipeline

```
┌─────────────────┐
│  Upload File    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Format Detection│
│  (PDF/Image)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Load Document  │
│  (Docling Core) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OCR Processing │
│  (Multi-engine) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Table Recognition│
│  (TableFormer)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Layout Analysis  │
│ (Headers/Paras) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Markdown Export  │
│  (Formatted)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Result   │
└─────────────────┘
```

### 5.5 Configuration

**Docling Configuration:**
```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True

converter = DocumentConverter(
    pipeline_options=pipeline_options
)
```

**OCR Engine Selection:**
- **Primary**: EasyOCR (best accuracy for tables)
- **Fallback**: RapidOCR (faster, lower resource)
- **Last Resort**: Tesseract (traditional OCR)

### 5.6 Deployment

#### 5.6.1 Hugging Face Spaces (Recommended)

**Advantages:**
- Free GPU/CPU hosting
- Automatic HTTPS
- CDN distribution
- Easy scaling

**Deployment Steps:**
1. Create new Space (Docker SDK)
2. Upload `Dockerfile`, `main.py`, `requirements.txt`
3. Add `README.md` with Space configuration:
```yaml
---
title: DocuFlow OCR Service
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---
```

#### 5.6.2 Local Docker Deployment

```bash
# Build
docker build -t docling-ocr ./ocr_service

# Run
docker run -d \
  --name docuflow-ocr \
  -p 7860:7860 \
  --restart unless-stopped \
  docling-ocr
```

#### 5.6.3 Cloud Deployment Options

**AWS Fargate:**
- Serverless container deployment
- Auto-scaling based on load
- Integrate with Application Load Balancer

**Google Cloud Run:**
- Pay-per-use pricing
- Automatic HTTPS
- Built-in load balancing

**Azure Container Instances:**
- Quick deployment
- Integration with Azure services

### 5.7 Performance Optimization

#### 5.7.1 Model Caching
```python
# Models downloaded during Docker build
RUN python -c "from docling.models import load_models; load_models()"
```

#### 5.7.2 Resource Management
- **CPU Mode**: 1-2 cores, 4GB RAM minimum
- **GPU Mode**: CUDA-enabled GPU, 8GB VRAM recommended
- **Processing Time**: 2-5 seconds per page (CPU), <1 second (GPU)

#### 5.7.3 Optimization Strategies
- Batch processing for multiple pages
- Async processing with job queue (future)
- Result caching for duplicate documents
- Image preprocessing for quality enhancement

### 5.8 Error Handling

**Common Errors:**
```python
# File format not supported
400 Bad Request: "Unsupported file format"

# File too large
413 Payload Too Large: "File exceeds maximum size"

# OCR processing failed
500 Internal Server Error: "OCR processing failed: [details]"

# Model loading failed
503 Service Unavailable: "OCR models not loaded"
```

### 5.9 Monitoring and Logging

**Logging Strategy:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log processing metrics
logger.info(f"Processing completed in {elapsed_time}ms")
logger.info(f"Extracted {page_count} pages, {table_count} tables")
```

**Future Enhancements:**
- Prometheus metrics endpoint
- Request tracing with correlation IDs
- Performance monitoring dashboard

## 6. Deployment Strategy

### 6.1 Main Application Deployment

#### 6.1.1 Multi-Stage Docker Build

The application uses an optimized multi-stage Dockerfile:

**Stage 1: Frontend Build**
```dockerfile
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# Output: /app/frontend/dist/
```

**Stage 2: Python Application**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./static
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Benefits:**
- Smaller final image (no Node.js in production)
- Faster deployment
- Single container for main app

#### 6.1.2 Docker Compose Setup

**Development Configuration:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app/backend  # Hot reload
      - ./uploads:/app/uploads  # Persist uploads
    environment:
      - OCR_SERVICE_URL=http://ocr:7860
    depends_on:
      - ocr

  ocr:
    build: ./ocr_service
    ports:
      - "7860:7860"
    volumes:
      - ./models:/root/.cache  # Cache models
```

**Production Configuration:**
```yaml
version: '3.8'

services:
  app:
    image: docuflow:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - OCR_SERVICE_URL=${OCR_SERVICE_URL}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - app
```

### 6.2 OCR Service Deployment

#### 6.2.1 Separate Deployment Rationale
- **Resource Isolation**: OCR requires significant CPU/GPU
- **Independent Scaling**: Scale OCR separately from main app
- **Cost Optimization**: Use specialized OCR hosting (HF Spaces with GPU)
- **Technology Flexibility**: Can swap OCR implementations

#### 6.2.2 Deployment Options Comparison

| Platform | Pros | Cons | Best For |
|----------|------|------|----------|
| **Hugging Face Spaces** | Free GPU, Easy setup, CDN | Public by default | MVP, Testing |
| **AWS Fargate** | Managed, Auto-scaling | Higher cost | Enterprise |
| **Google Cloud Run** | Pay-per-use, Fast | Cold starts | Variable load |
| **Self-hosted Docker** | Full control, No external deps | Maintenance overhead | On-premise |

### 6.3 Platform-Specific Deployment

#### 6.3.1 Railway Deployment
See [RAILWAY.md](RAILWAY.md) for detailed instructions.

**Quick Steps:**
1. Connect GitHub repository
2. Add environment variables
3. Deploy from `main` branch
4. Railway auto-detects Dockerfile

**Configuration:**
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

#### 6.3.2 Koyeb Deployment
See [DOCKER_KOYEB.md](DOCKER_KOYEB.md) for detailed instructions.

#### 6.3.3 Heroku Deployment

**Procfile:**
```
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**heroku.yml:**
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

#### 6.3.4 DigitalOcean App Platform

**app.yaml:**
```yaml
name: docuflow
services:
  - name: web
    github:
      repo: Sanali209/DocuFlow-
      branch: main
    dockerfile_path: Dockerfile
    http_port: 8000
    routes:
      - path: /
    envs:
      - key: OCR_SERVICE_URL
        value: ${OCR_SERVICE_URL}
```

### 6.4 Production Checklist

#### 6.4.1 Pre-Deployment
- [ ] Set environment variables (OCR_SERVICE_URL, etc.)
- [ ] Configure database backup strategy
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS for production domain
- [ ] Set appropriate file upload limits
- [ ] Configure log rotation
- [ ] Set up monitoring and alerts

#### 6.4.2 Security Hardening
- [ ] Use HTTPS only
- [ ] Implement rate limiting
- [ ] Add CSRF protection
- [ ] Configure secure headers
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Database access restrictions

#### 6.4.3 Performance Tuning
- [ ] Enable response compression
- [ ] Configure CDN for static assets
- [ ] Optimize database queries
- [ ] Implement caching strategy
- [ ] Set up load balancing
- [ ] Configure auto-scaling

### 6.5 Backup and Recovery

#### 6.5.1 Database Backup
```bash
# SQLite backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 /app/data/documents.db ".backup '${BACKUP_DIR}/documents_${DATE}.db'"

# Keep last 30 days
find ${BACKUP_DIR} -name "documents_*.db" -mtime +30 -delete
```

#### 6.5.2 Upload Files Backup
```bash
# Rsync uploads directory
rsync -avz /app/uploads/ backup-server:/backups/docuflow-uploads/
```

#### 6.5.3 Automated Backup Schedule
```cron
# Daily database backup at 2 AM
0 2 * * * /scripts/backup-database.sh

# Weekly full backup at 3 AM Sunday
0 3 * * 0 /scripts/full-backup.sh
```

### 6.6 Monitoring and Observability

#### 6.6.1 Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_database_connection(),
        "ocr_service": check_ocr_service(),
        "version": "1.0.0"
    }
```

#### 6.6.2 Metrics to Monitor
- API response times
- Database query performance
- OCR processing duration
- Error rates
- Upload file sizes
- Active connections
- Memory usage
- CPU utilization

#### 6.6.3 Logging Strategy
```python
import logging

# Structured logging
logger.info(
    "Document created",
    extra={
        "document_id": doc.id,
        "user": request.user.email,
        "action": "create"
    }
)
```

### 6.7 Continuous Integration/Deployment

#### 6.7.1 GitHub Actions Workflow
```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          pip install -r backend/requirements.txt
          pytest backend/
      
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t docuflow:${{ github.sha }} .
      
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          # Deployment script
```

## 7. Development Workflow

### 7.1 Development Environment Setup

#### 7.1.1 Prerequisites
- Python 3.12+
- Node.js 22+
- Docker and Docker Compose
- Git

#### 7.1.2 Initial Setup
```bash
# Clone repository
git clone https://github.com/Sanali209/DocuFlow-.git
cd DocuFlow-

# Backend setup
pip install -r backend/requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# OCR service (optional for development)
cd ocr_service
docker build -t docling-ocr .
docker run -d -p 7860:7860 docling-ocr
cd ..
```

### 7.2 Development Servers

#### 7.2.1 Backend Development
```bash
# Run with hot reload
uvicorn backend.main:app --reload --port 8000 --log-level debug

# Access points:
# - API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

#### 7.2.2 Frontend Development
```bash
cd frontend
npm run dev

# Vite dev server: http://localhost:5173
# Features:
# - Hot Module Replacement (HMR)
# - Fast compilation
# - Source maps for debugging
```

#### 7.2.3 Full Stack Development
```bash
# Terminal 1: Backend
uvicorn backend.main:app --reload

# Terminal 2: Frontend  
cd frontend && npm run dev

# Terminal 3: OCR Service (if testing OCR)
docker run -p 7860:7860 docling-ocr
```

### 7.3 Testing Strategy

#### 7.3.1 Backend Testing

**Unit Tests:**
```bash
cd backend
pytest test_main.py -v
pytest test_features.py -v
pytest test_settings.py -v
```

**Integration Tests:**
```bash
pytest test_attachment_update.py -v
```

**Coverage Report:**
```bash
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

#### 7.3.2 Frontend Testing (Future)
```bash
cd frontend
npm run test        # Run tests
npm run test:watch  # Watch mode
npm run test:coverage
```

#### 7.3.3 E2E Testing (Future)
```bash
# Playwright or Cypress
npm run test:e2e
```

### 7.4 Code Quality

#### 7.4.1 Python Code Style
```bash
# Format code
black backend/

# Check style
flake8 backend/

# Type checking
mypy backend/
```

#### 7.4.2 JavaScript Code Style
```bash
cd frontend
npm run lint        # ESLint
npm run format      # Prettier
```

### 7.5 Database Management

#### 7.5.1 Schema Migrations
Currently handled via ALTER TABLE statements in `main.py`:
```python
# Migration pattern
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN new_field TEXT"))
        conn.commit()
    except Exception:
        pass  # Column already exists
```

#### 7.5.2 Future: Alembic Migrations
```bash
# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head
```

#### 7.5.3 Database Inspection
```bash
# SQLite command line
sqlite3 documents.db

# Useful commands:
.tables                    # List tables
.schema documents          # Show table structure
SELECT * FROM documents;   # Query data
```

### 7.6 Git Workflow

#### 7.6.1 Branch Strategy
```
main                    # Production-ready code
├── develop            # Integration branch
├── feature/xxx        # Feature branches
├── bugfix/xxx         # Bug fixes
└── hotfix/xxx         # Production hotfixes
```

#### 7.6.2 Commit Guidelines
```bash
# Format: <type>(<scope>): <subject>

# Types:
feat: New feature
fix: Bug fix
docs: Documentation changes
style: Code style changes
refactor: Code refactoring
test: Test additions/changes
chore: Build process, dependencies

# Examples:
git commit -m "feat(ocr): Add multi-page PDF support"
git commit -m "fix(api): Handle null assignee in tasks"
git commit -m "docs(readme): Update deployment instructions"
```

### 7.7 Debugging

#### 7.7.1 Backend Debugging
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use FastAPI's debug mode
@app.get("/debug")
async def debug():
    return {"debug": "info"}
```

#### 7.7.2 Frontend Debugging
```javascript
// Browser DevTools
console.log('Debug:', data);
debugger;  // Breakpoint

// Svelte DevTools (browser extension)
// - Component hierarchy
// - State inspection
// - Event tracking
```

#### 7.7.3 Network Debugging
```bash
# Check API calls
curl -X GET http://localhost:8000/documents/

# Test OCR service
curl -X POST http://localhost:7860/convert \
  -F "file=@test.pdf"
```

### 7.8 Performance Profiling

#### 7.8.1 Backend Profiling
```python
import cProfile
import pstats

# Profile endpoint
@app.get("/profile")
async def profile():
    profiler = cProfile.Profile()
    profiler.enable()
    # ... code to profile ...
    profiler.disable()
    stats = pstats.Stats(profiler)
    return stats.get_stats()
```

#### 7.8.2 Frontend Profiling
```javascript
// React DevTools Profiler (for component analysis)
// Lighthouse for performance audits
// Chrome DevTools Performance tab
```

## 8. Future Enhancements

### 8.1 Planned Features

#### 8.1.1 Authentication & Authorization
- **User Management**: Registration, login, profile
- **JWT Authentication**: Token-based API access
- **Role-Based Access Control**: Admin, Editor, Viewer roles
- **Document Permissions**: Public, private, shared documents
- **Team Collaboration**: Shared workspaces

#### 8.1.2 Advanced Features
- **Document Versioning**: Track changes over time
- **Document Templates**: Pre-defined document structures
- **Workflow Automation**: Auto-status updates, notifications
- **Advanced Search**: Elasticsearch integration
- **Analytics Dashboard**: Document metrics, usage stats
- **Export Functionality**: PDF, Excel, CSV exports
- **Email Integration**: Send documents, notifications
- **Webhooks**: Event-driven integrations
- **API Webhooks**: Real-time updates to external systems

#### 8.1.3 Mobile Applications
- **React Native App**: iOS and Android native apps
- **Offline Support**: Local storage, sync when online
- **Camera Integration**: Direct document scanning
- **Push Notifications**: Task reminders, updates

#### 8.1.4 Database Enhancements
- **PostgreSQL Migration**: Better concurrency, scalability
- **Database Replication**: High availability
- **Full-Text Search**: Postgres FTS or Elasticsearch
- **Database Sharding**: Horizontal scaling

#### 8.1.5 OCR Improvements
- **Language Support**: Multi-language OCR
- **Handwriting Recognition**: Support handwritten documents
- **Form Recognition**: Extract form fields
- **Signature Detection**: Identify and extract signatures
- **Document Classification**: Auto-categorize documents

### 8.2 Technical Debt

#### 8.2.1 Code Improvements
- Implement proper client-side routing
- Add comprehensive error boundaries
- Improve type safety (TypeScript migration?)
- Refactor large components
- Add more unit tests
- Implement integration test suite
- Add E2E test coverage

#### 8.2.2 Infrastructure Improvements
- Implement Redis caching
- Add message queue (Celery/RQ)
- Set up CDN for static assets
- Implement proper logging system
- Add monitoring and alerting
- Set up CI/CD pipeline
- Automated database migrations

#### 8.2.3 Documentation Improvements
- API documentation with examples
- Architecture decision records (ADRs)
- Deployment runbooks
- Troubleshooting guides
- Video tutorials
- API client libraries

### 8.3 Scalability Roadmap

#### 8.3.1 Horizontal Scaling
```
┌─────────────┐
│ Load Balancer│
└──────┬───────┘
       │
       ├─────────────┬─────────────┬─────────────┐
       ▼             ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  App 1   │  │  App 2   │  │  App 3   │  │  App N   │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │             │
     └─────────────┴─────────────┴─────────────┘
                    │
            ┌───────▼────────┐
            │   PostgreSQL   │
            │   (Primary)    │
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │   PostgreSQL   │
            │   (Replica)    │
            └────────────────┘
```

#### 8.3.2 Microservices Evolution
- Extract user service
- Separate notification service
- Dedicated search service
- Analytics service
- File storage service (S3)

## 9. Appendix

### 9.1 Technology Choices Rationale

#### 9.1.1 Why FastAPI?
- **Performance**: Async support, high throughput
- **Developer Experience**: Auto-generated API docs
- **Type Safety**: Pydantic validation
- **Modern Python**: Python 3.12+ features
- **Ecosystem**: Rich plugin ecosystem

#### 9.1.2 Why Svelte 5?
- **Performance**: No virtual DOM overhead
- **Bundle Size**: Smaller than React/Vue
- **Developer Experience**: Less boilerplate
- **Reactivity**: Built-in reactive system
- **Modern**: Runes API is cutting-edge

#### 9.1.3 Why SQLite (for now)?
- **Simplicity**: Zero configuration
- **Portability**: Single file database
- **Performance**: Sufficient for small-medium loads
- **Easy Migration**: Can upgrade to Postgres later

#### 9.1.4 Why Separate OCR Service?
- **Resource Isolation**: OCR is resource-intensive
- **Scalability**: Scale independently
- **Technology Freedom**: Can swap implementations
- **Cost Optimization**: Use specialized hosting

### 9.2 Glossary

- **OCR**: Optical Character Recognition
- **ORM**: Object-Relational Mapping
- **CRUD**: Create, Read, Update, Delete
- **HMR**: Hot Module Replacement
- **JWT**: JSON Web Token
- **CORS**: Cross-Origin Resource Sharing
- **CDN**: Content Delivery Network
- **ASGI**: Asynchronous Server Gateway Interface
- **API**: Application Programming Interface
- **REST**: Representational State Transfer

### 9.3 References

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Svelte Documentation**: https://svelte.dev/docs
- **IBM Docling**: https://github.com/docling
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Docker Documentation**: https://docs.docker.com/

---

**Document Version**: 2.0  
**Last Updated**: 2026-01-29  
**Author**: DocuFlow Development Team
