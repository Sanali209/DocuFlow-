# API Documentation

Complete REST API reference for DocuFlow.

## Base URL

```
# Development
http://localhost:8000

# Production
https://your-domain.com
```

## Authentication

Currently, DocuFlow does not require authentication. All endpoints are publicly accessible.

**Future**: JWT-based authentication will be added in a future release.

## Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## API Endpoints

### Documents

#### List Documents

Get all documents with optional filtering and search.

```http
GET /documents/
```

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in name, description, content |
| `type` | string | Filter by document type |
| `status` | string | Filter by status |
| `tag` | string | Filter by tag name |
| `assignee` | string | Filter by task assignee |
| `reg_date_from` | date | Registration date start (YYYY-MM-DD) |
| `reg_date_to` | date | Registration date end (YYYY-MM-DD) |
| `done_date_from` | date | Done date start (YYYY-MM-DD) |
| `done_date_to` | date | Done date end (YYYY-MM-DD) |
| `task_statuses` | string | Comma-separated task statuses |
| `sort` | string | Sort field (default: `-registration_date`) |

**Example Request**:

```bash
curl "http://localhost:8000/documents/?search=project&type=Plan&status=In+Progress"
```

**Example Response**:

```json
[
  {
    "id": 1,
    "name": "Project Plan Q1 2024",
    "description": "Quarterly planning document",
    "type": "Plan",
    "status": "In Progress",
    "registration_date": "2024-01-15",
    "done_date": null,
    "author": "John Doe",
    "content": "# Project Overview\n\nGoals for Q1...",
    "tasks": [
      {
        "id": 1,
        "name": "Define objectives",
        "status": "Done",
        "assignee": "Jane Smith",
        "order_index": 0
      }
    ],
    "tags": [
      {"id": 1, "name": "planning"},
      {"id": 2, "name": "q1"}
    ],
    "journal_entries": [
      {
        "id": 1,
        "entry_text": "Initial draft completed",
        "created_at": "2024-01-16T10:30:00"
      }
    ],
    "attachments": [
      {
        "id": 1,
        "filename": "diagram.png",
        "filepath": "uploads/abc123_diagram.png",
        "uploaded_at": "2024-01-15T14:20:00"
      }
    ]
  }
]
```

**Response Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid query parameters
- `500 Internal Server Error`: Server error

#### Get Document

Get a single document by ID.

```http
GET /documents/{id}
```

**Path Parameters**:
- `id` (integer, required): Document ID

**Example Request**:

```bash
curl http://localhost:8000/documents/1
```

**Response**: Same structure as single document in list response.

#### Create Document

Create a new document.

```http
POST /documents/
Content-Type: application/json
```

**Request Body**:

```json
{
  "name": "New Project Plan",
  "description": "Description text",
  "type": "Plan",
  "status": "In Progress",
  "registration_date": "2024-01-20",
  "done_date": null,
  "author": "John Doe",
  "content": "# Content\n\nMarkdown content here"
}
```

**Required Fields**:
- `name`: string
- `type`: string
- `status`: string

**Optional Fields**:
- `description`: string
- `registration_date`: date (defaults to today)
- `done_date`: date
- `author`: string
- `content`: string

**Example Request**:

```bash
curl -X POST http://localhost:8000/documents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Document",
    "type": "Plan",
    "status": "In Progress"
  }'
```

**Response**: `201 Created` with created document object.

#### Update Document

Update an existing document.

```http
PUT /documents/{id}
Content-Type: application/json
```

**Request Body**: Same as create, all fields optional.

**Example Request**:

```bash
curl -X PUT http://localhost:8000/documents/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Done",
    "done_date": "2024-01-25"
  }'
```

**Response**: `200 OK` with updated document object.

#### Delete Document

Delete a document and all associated data (tasks, notes, attachments).

```http
DELETE /documents/{id}
```

**Example Request**:

```bash
curl -X DELETE http://localhost:8000/documents/1
```

**Response**: `204 No Content`

#### Scan Document (OCR)

Upload files for OCR processing and extract text/tables.

```http
POST /documents/scan
Content-Type: multipart/form-data
```

**Form Data**:
- `files`: File[] (one or more files)
- `document_id`: integer (optional, to append to existing document)

**Example Request**:

```bash
curl -X POST http://localhost:8000/documents/scan \
  -F "files=@document1.pdf" \
  -F "files=@document2.jpg"
```

**Example Response**:

```json
{
  "extracted_text": "# Extracted Content\n\n| Header 1 | Header 2 |\n|----------|----------|\n| Data 1   | Data 2   |",
  "extracted_name": "Auto-detected Document Name",
  "attachments": [
    {
      "id": 1,
      "filename": "document1.pdf",
      "filepath": "uploads/xyz789_document1.pdf"
    }
  ]
}
```

**Response Codes**:
- `200 OK`: Scanning successful
- `400 Bad Request`: Invalid file format
- `503 Service Unavailable`: OCR service not available

### Tasks

#### List Document Tasks

Get all tasks for a specific document.

```http
GET /documents/{document_id}/tasks
```

**Example Request**:

```bash
curl http://localhost:8000/documents/1/tasks
```

**Response**:

```json
[
  {
    "id": 1,
    "document_id": 1,
    "name": "Review document",
    "status": "Pending",
    "assignee": "Jane Doe",
    "order_index": 0
  }
]
```

#### Create Task

Add a task to a document.

```http
POST /documents/{document_id}/tasks
Content-Type: application/json
```

**Request Body**:

```json
{
  "name": "New task",
  "status": "Planned",
  "assignee": "John Doe"
}
```

**Required**: `name`, `status`  
**Optional**: `assignee`

**Status Values**: `Planned`, `Pending`, `Done`

**Example Request**:

```bash
curl -X POST http://localhost:8000/documents/1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Complete review",
    "status": "Pending",
    "assignee": "Jane Smith"
  }'
```

**Response**: `201 Created` with created task object.

#### Update Task

Update a task's details.

```http
PUT /tasks/{task_id}
Content-Type: application/json
```

**Request Body**: All fields optional

```json
{
  "name": "Updated task name",
  "status": "Done",
  "assignee": "New Assignee"
}
```

**Example Request**:

```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "Done"}'
```

**Response**: `200 OK` with updated task object.

#### Delete Task

Remove a task from a document.

```http
DELETE /documents/{document_id}/tasks/{task_id}
```

**Example Request**:

```bash
curl -X DELETE http://localhost:8000/documents/1/tasks/1
```

**Response**: `204 No Content`

### Tags

#### List All Tags

Get all available tags in the system.

```http
GET /tags
```

**Example Request**:

```bash
curl http://localhost:8000/tags
```

**Response**:

```json
[
  {"id": 1, "name": "urgent"},
  {"id": 2, "name": "financial"},
  {"id": 3, "name": "planning"}
]
```

**Note**: Tags are automatically created when assigned to documents. There's no explicit tag creation endpoint.

### Journal Entries

#### Create Journal Entry

Add a note/journal entry to a document.

```http
POST /documents/{document_id}/journal
Content-Type: application/json
```

**Request Body**:

```json
{
  "entry_text": "Meeting notes: Discussed project timeline..."
}
```

**Example Request**:

```bash
curl -X POST http://localhost:8000/documents/1/journal \
  -H "Content-Type: application/json" \
  -d '{
    "entry_text": "Status update: 50% complete"
  }'
```

**Response**: `201 Created` with journal entry object including timestamp.

### Attachments

#### Upload Attachment

Add a file attachment to a document.

```http
POST /documents/{document_id}/attachments
Content-Type: multipart/form-data
```

**Form Data**:
- `file`: File (PDF, JPEG, PNG, JPG)

**Example Request**:

```bash
curl -X POST http://localhost:8000/documents/1/attachments \
  -F "file=@report.pdf"
```

**Response**:

```json
{
  "id": 1,
  "filename": "report.pdf",
  "filepath": "uploads/def456_report.pdf",
  "uploaded_at": "2024-01-20T15:30:00"
}
```

#### Download Attachment

Retrieve an uploaded file.

```http
GET /uploads/{filepath}
```

**Example Request**:

```bash
curl http://localhost:8000/uploads/def456_report.pdf -o report.pdf
```

**Response**: File stream with appropriate Content-Type header.

### Filter Presets

#### List Presets

Get all saved filter presets.

```http
GET /filter-presets
```

**Response**:

```json
[
  {
    "id": 1,
    "name": "Urgent Tasks",
    "filters": {
      "status": "In Progress",
      "tag": "urgent",
      "task_statuses": ["Pending", "Planned"]
    },
    "created_at": "2024-01-15T10:00:00"
  }
]
```

#### Create Preset

Save a filter configuration.

```http
POST /filter-presets
Content-Type: application/json
```

**Request Body**:

```json
{
  "name": "My Custom Filter",
  "filters": {
    "type": "Plan",
    "status": "In Progress",
    "tag": "project-alpha"
  }
}
```

**Response**: `201 Created` with preset object.

#### Delete Preset

Remove a saved filter preset.

```http
DELETE /filter-presets/{id}
```

**Response**: `204 No Content`

### Settings

#### Get Setting

Retrieve a configuration setting.

```http
GET /settings/{key}
```

**Common Keys**:
- `ocr_url`: OCR service endpoint
- `doc_name_regex`: Document name extraction pattern

**Example Request**:

```bash
curl http://localhost:8000/settings/ocr_url
```

**Response**:

```json
{
  "key": "ocr_url",
  "value": "http://localhost:7860"
}
```

#### Update Setting

Change a configuration setting.

```http
PUT /settings/{key}
Content-Type: application/json
```

**Request Body**:

```json
{
  "value": "https://my-ocr-service.com"
}
```

**Example Request**:

```bash
curl -X PUT http://localhost:8000/settings/ocr_url \
  -H "Content-Type: application/json" \
  -d '{"value": "http://localhost:7860"}'
```

**Response**: `200 OK` with updated setting.

### Health Check

#### Application Health

Check if the application is running.

```http
GET /health
```

**Response**:

```json
{
  "status": "healthy"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

**Common Status Codes**:
- `400 Bad Request`: Invalid input data
- `404 Not Found`: Resource doesn't exist
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: External service (OCR) unavailable

## Rate Limiting

Currently, there are no rate limits. This may change in future releases.

## CORS

CORS is configured to allow requests from any origin in development. Configure appropriately for production.

## Pagination

**Current**: All results returned in a single response.

**Future**: Pagination will be added with `limit` and `offset` parameters:
```
GET /documents/?limit=50&offset=100
```

## Webhooks

**Status**: Not yet implemented

**Future**: Webhook support for events like:
- Document created
- Document updated
- Task completed
- Scan completed

## Client Libraries

**Official Libraries**: Coming soon

**Language Support Planned**:
- Python SDK
- JavaScript/TypeScript SDK
- Go SDK

**Current**: Use standard HTTP libraries:

**Python Example**:
```python
import requests

# List documents
response = requests.get('http://localhost:8000/documents/')
documents = response.json()

# Create document
new_doc = {
    'name': 'Test Document',
    'type': 'Plan',
    'status': 'In Progress'
}
response = requests.post(
    'http://localhost:8000/documents/',
    json=new_doc
)
```

**JavaScript Example**:
```javascript
// List documents
const response = await fetch('http://localhost:8000/documents/');
const documents = await response.json();

// Create document
const newDoc = {
  name: 'Test Document',
  type: 'Plan',
  status: 'In Progress'
};
const response = await fetch('http://localhost:8000/documents/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(newDoc)
});
```

## Best Practices

### Error Handling

Always check response status codes and handle errors gracefully:

```python
response = requests.get('http://localhost:8000/documents/999')
if response.status_code == 404:
    print("Document not found")
elif response.status_code == 200:
    document = response.json()
else:
    print(f"Error: {response.status_code}")
```

### File Uploads

Use streaming for large files:

```python
with open('large-file.pdf', 'rb') as f:
    files = {'files': f}
    response = requests.post(
        'http://localhost:8000/documents/scan',
        files=files
    )
```

### Date Formats

Always use ISO 8601 format for dates: `YYYY-MM-DD`

```json
{
  "registration_date": "2024-01-20",
  "done_date": "2024-01-25"
}
```

### Batch Operations

For multiple operations, send requests in parallel:

```python
import concurrent.futures
import requests

def create_document(doc_data):
    return requests.post(
        'http://localhost:8000/documents/',
        json=doc_data
    )

documents = [
    {'name': 'Doc 1', 'type': 'Plan', 'status': 'In Progress'},
    {'name': 'Doc 2', 'type': 'Report', 'status': 'Done'},
]

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(create_document, documents)
```

## Additional Resources

- [Swagger UI](http://localhost:8000/docs) - Interactive API testing
- [ReDoc](http://localhost:8000/redoc) - Alternative API documentation
- [User Guide](User-Guide.md) - Feature documentation
- [Developer Guide](Developer-Guide.md) - Development workflow

---

[← Back to User Guide](User-Guide.md) | [Next: Deployment Guide →](Deployment-Guide.md)
