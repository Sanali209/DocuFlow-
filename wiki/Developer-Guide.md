# Developer Guide

Welcome to the DocuFlow Developer Guide. This document provides comprehensive information for developers working on DocuFlow.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Code Style Guidelines](#code-style-guidelines)
4. [Testing Strategies](#testing-strategies)
5. [Database Management](#database-management)
6. [Git Workflow](#git-workflow)
7. [Debugging Tips](#debugging-tips)
8. [Common Development Tasks](#common-development-tasks)

---

## Development Environment Setup

### Prerequisites

Ensure you have the required tools installed:

- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **Node.js 22+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)
- **Docker & Docker Compose** (Optional) - [Download](https://www.docker.com/)
- **IDE/Editor** - VS Code, PyCharm, or your preferred editor

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/Sanali209/DocuFlow-.git
cd DocuFlow-

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Svelte for VS Code
- ESLint
- Prettier
- Docker
- Thunder Client (API testing)

**settings.json:**
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "[svelte]": {
    "editor.defaultFormatter": "svelte.svelte-vscode"
  }
}
```

#### PyCharm

Configure:
1. Set Python interpreter to your virtual environment
2. Enable pytest as test runner
3. Configure Black as code formatter
4. Enable Flake8 for linting

### Running Development Servers

#### Terminal 1: Backend

```bash
# From project root
uvicorn backend.main:app --reload --port 8000

# With debug logging
uvicorn backend.main:app --reload --port 8000 --log-level debug

# Custom host
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- API: http://localhost:8000
- Interactive API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at:
- Application: http://localhost:5173

Hot module replacement (HMR) is enabled for instant updates.

#### Terminal 3: OCR Service (Optional)

```bash
# Build OCR service
docker build -t docling-ocr ./ocr_service

# Run OCR service
docker run -p 7860:7860 docling-ocr

# Or with docker-compose
docker-compose up ocr-service
```

### Environment Variables

Create `.env` files for local development:

**Backend (.env in project root):**
```env
OCR_SERVICE_URL=http://localhost:7860
DOC_NAME_REGEX=(?si)Order:\s*(.*?)\s*Date:
DATABASE_URL=sqlite:///./data/sql_app.db
```

**Frontend (frontend/.env):**
```env
VITE_API_URL=http://localhost:8000
```

---

## Project Structure

```
DocuFlow-/
├── backend/                    # FastAPI backend application
│   ├── main.py                # Application entry point & routes
│   ├── models.py              # SQLAlchemy database models
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── crud.py                # Database CRUD operations
│   ├── database.py            # Database configuration
│   ├── requirements.txt       # Python dependencies
│   ├── test_main.py          # Main API tests
│   ├── test_features.py      # Feature-specific tests
│   ├── test_settings.py      # Settings tests
│   └── test_attachment_update.py  # Attachment tests
│
├── frontend/                   # Svelte 5 frontend application
│   ├── src/                   # Source files
│   │   ├── App.svelte        # Root component
│   │   ├── main.js           # Application entry
│   │   └── components/       # Reusable components
│   │       ├── DocumentCard.svelte
│   │       ├── DocumentForm.svelte
│   │       ├── FilterPanel.svelte
│   │       └── ...
│   ├── public/               # Static assets
│   ├── index.html            # HTML entry point
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite configuration
│   └── svelte.config.js      # Svelte configuration
│
├── ocr_service/               # OCR microservice
│   ├── main.py               # FastAPI OCR endpoints
│   ├── preprocessing.py      # Image preprocessing
│   ├── requirements.txt      # OCR dependencies
│   └── Dockerfile            # OCR service container
│
├── static/                    # Production frontend build
│   └── uploads/              # User-uploaded files
│
├── docs/                      # Additional documentation
├── wiki/                      # Wiki documentation
├── verification/              # Test verification files
│
├── Dockerfile                 # Main application container
├── docker-compose.yml         # Multi-container setup
├── .dockerignore             # Docker build exclusions
├── .gitignore                # Git exclusions
├── README.md                 # Project overview
└── designdoc.md              # Technical design document
```

### Key Files Explained

#### Backend

**main.py**
- FastAPI application instance
- All API route definitions
- CORS middleware configuration
- Database migrations on startup
- Static file serving

**models.py**
- SQLAlchemy ORM models
- Database table definitions
- Relationships between entities

**schemas.py**
- Pydantic models for request validation
- Response serialization
- Type definitions

**crud.py**
- Database query functions
- CRUD operations abstraction
- Business logic layer

**database.py**
- Database engine configuration
- Session management
- Connection pooling

#### Frontend

**App.svelte**
- Root component
- State management using Svelte Runes
- Main layout and routing

**Components**
- Reusable UI components
- Each component handles specific functionality
- Props-based communication

**Vite Configuration**
- Build optimization
- Dev server settings
- Plugin configuration

---

## Code Style Guidelines

### Python (Backend)

#### Follow PEP 8

```python
# Good: descriptive names, proper spacing
def create_document(db: Session, document: schemas.DocumentCreate):
    """Create a new document in the database."""
    db_document = models.Document(**document.dict())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

# Bad: poor naming, inconsistent spacing
def cd(d,doc):
    x=models.Document(**doc.dict())
    d.add(x)
    d.commit()
    return x
```

#### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import List, Optional

def get_documents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[models.Document]:
    query = db.query(models.Document)
    if search:
        query = query.filter(models.Document.name.contains(search))
    return query.offset(skip).limit(limit).all()
```

#### Docstrings

Use Google-style docstrings:

```python
def update_document(db: Session, document_id: int, updates: dict) -> Optional[models.Document]:
    """
    Update a document with new values.

    Args:
        db: Database session
        document_id: ID of document to update
        updates: Dictionary of fields to update

    Returns:
        Updated document object or None if not found

    Raises:
        ValueError: If updates contain invalid fields
    """
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        return None
    
    for key, value in updates.items():
        setattr(document, key, value)
    
    db.commit()
    db.refresh(document)
    return document
```

#### Error Handling

```python
# Good: Specific exceptions with context
@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document with id {document_id} not found"
        )
    crud.delete_document(db, document_id)
    return {"message": "Document deleted successfully"}

# Bad: Generic errors
@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_document(db, document_id)
        return {"ok": True}
    except:
        return {"ok": False}
```

#### Code Formatting

Use Black for automatic formatting:

```bash
# Format all backend files
black backend/

# Check without modifying
black --check backend/

# Format specific file
black backend/main.py
```

#### Linting

Use Flake8 for linting:

```bash
# Lint backend
flake8 backend/ --max-line-length=100

# With specific rules
flake8 backend/ --ignore=E501,W503
```

### JavaScript/Svelte (Frontend)

#### Use Prettier

```bash
# Format all frontend files
cd frontend
npm run format

# Check formatting
npm run format:check
```

**.prettierrc:**
```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

#### Svelte Component Structure

```svelte
<script>
  // 1. Imports
  import { onMount } from 'svelte';
  
  // 2. Props
  export let documentId;
  export let onSave = () => {};
  
  // 3. State (Svelte 5 Runes)
  let name = $state('');
  let description = $state('');
  
  // 4. Derived state
  let isValid = $derived(name.length > 0);
  
  // 5. Functions
  function handleSubmit() {
    if (!isValid) return;
    onSave({ name, description });
  }
  
  // 6. Lifecycle
  onMount(() => {
    // Initialization
  });
</script>

<!-- 7. Markup -->
<div class="document-form">
  <input bind:value={name} placeholder="Document name" />
  <textarea bind:value={description} placeholder="Description" />
  <button onclick={handleSubmit} disabled={!isValid}>Save</button>
</div>

<!-- 8. Styles -->
<style>
  .document-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
</style>
```

#### Naming Conventions

```javascript
// Components: PascalCase
import DocumentCard from './DocumentCard.svelte';

// Variables and functions: camelCase
let documentList = [];
function fetchDocuments() { }

// Constants: UPPER_SNAKE_CASE
const API_BASE_URL = 'http://localhost:8000';

// Files: kebab-case
// document-card.svelte
// api-client.js
```

### Git Commit Messages

Follow Conventional Commits:

```bash
# Format
<type>(<scope>): <subject>

# Types
feat: New feature
fix: Bug fix
docs: Documentation changes
style: Code style changes (formatting)
refactor: Code refactoring
test: Adding or updating tests
chore: Maintenance tasks

# Examples
feat(backend): add document filtering by date range
fix(frontend): resolve mobile menu navigation issue
docs(wiki): update deployment guide with Heroku instructions
refactor(ocr): optimize image preprocessing pipeline
test(backend): add tests for attachment endpoints
```

---

## Testing Strategies

### Backend Testing

#### Running Tests

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_main.py

# Run specific test
pytest test_main.py::test_create_document

# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s
```

#### Test Structure

```python
# test_documents.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app, get_db
from backend.database import Base
from backend import models, schemas

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """Create test client."""
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

def test_create_document(client):
    """Test creating a new document."""
    response = client.post(
        "/documents/",
        json={
            "name": "Test Document",
            "type": "Plan",
            "status": "In Progress",
            "author": "Test User",
            "description": "Test description"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Document"
    assert "id" in data

def test_get_documents(client):
    """Test retrieving documents."""
    # Create test document
    client.post("/documents/", json={"name": "Doc 1", "type": "Plan"})
    
    # Get documents
    response = client.get("/documents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Doc 1"

def test_document_not_found(client):
    """Test 404 for non-existent document."""
    response = client.get("/documents/9999")
    assert response.status_code == 404
```

#### Existing Tests

The project includes several test files:

**test_main.py**: Core API functionality
- Document CRUD operations
- Basic filtering
- Health checks

**test_features.py**: Advanced features
- Task management
- Notes
- Tags
- Filtering

**test_settings.py**: Settings management
- Reading/updating settings
- Default values

**test_attachment_update.py**: File attachments
- Upload functionality
- Attachment management

### Frontend Testing

While comprehensive frontend tests aren't currently implemented, here's how to add them:

#### Setup Vitest

```bash
cd frontend
npm install -D vitest @testing-library/svelte @testing-library/jest-dom
```

**vite.config.js:**
```javascript
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte({ hot: !process.env.VITEST })],
  test: {
    globals: true,
    environment: 'jsdom',
  },
});
```

#### Example Component Test

```javascript
// DocumentCard.test.js
import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import DocumentCard from './DocumentCard.svelte';

describe('DocumentCard', () => {
  it('renders document information', () => {
    const document = {
      id: 1,
      name: 'Test Doc',
      type: 'Plan',
      status: 'Done',
      author: 'John Doe',
    };

    render(DocumentCard, { props: { document } });

    expect(screen.getByText('Test Doc')).toBeInTheDocument();
    expect(screen.getByText('Plan')).toBeInTheDocument();
  });

  it('calls onDelete when delete button clicked', async () => {
    const onDelete = vi.fn();
    const document = { id: 1, name: 'Test' };

    render(DocumentCard, { props: { document, onDelete } });

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    await fireEvent.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith(1);
  });
});
```

### Integration Testing

Test the full stack with Docker Compose:

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run integration tests
pytest tests/integration/

# Cleanup
docker-compose down
```

### Test Coverage Goals

- Backend: Aim for >80% coverage
- Critical paths: 100% coverage (CRUD operations, authentication)
- UI components: Test user interactions and state changes

---

## Database Management

### Database Schema

The application uses SQLAlchemy ORM with SQLite (development) or PostgreSQL (production).

#### Models Overview

**Document Model:**
```python
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)
    status = Column(String)
    author = Column(String)
    description = Column(Text)
    content = Column(Text)  # OCR extracted text
    registration_date = Column(Date)
    done_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = relationship("Tag", secondary="document_tags", back_populates="documents")
    tasks = relationship("Task", back_populates="document", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="document", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="document", cascade="all, delete-orphan")
```

**Task Model:**
```python
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    name = Column(String)
    status = Column(String)  # Planned, Pending, Done
    assignee = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="tasks")
```

### Migrations

DocuFlow uses runtime migrations in `main.py`:

```python
# Add new column
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN new_field TEXT"))
        conn.commit()
    except Exception:
        pass  # Column already exists
```

#### Adding a New Field

1. Update model in `models.py`:
```python
class Document(Base):
    # ... existing fields ...
    priority = Column(String, default="Medium")  # New field
```

2. Add migration in `main.py`:
```python
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN priority TEXT DEFAULT 'Medium'"))
        conn.commit()
    except Exception:
        pass
```

3. Update schema in `schemas.py`:
```python
class DocumentBase(BaseModel):
    # ... existing fields ...
    priority: Optional[str] = "Medium"
```

4. Update CRUD operations in `crud.py` if needed

### Database Inspection

```bash
# SQLite
sqlite3 data/sql_app.db

# List tables
.tables

# Describe table
.schema documents

# Query data
SELECT * FROM documents LIMIT 10;

# Exit
.quit
```

### Database Reset

```bash
# Development only - deletes all data!
rm data/sql_app.db

# Restart backend to recreate
uvicorn backend.main:app --reload
```

### Backup and Restore

```bash
# Backup
cp data/sql_app.db data/sql_app.db.backup

# Restore
cp data/sql_app.db.backup data/sql_app.db

# Export to SQL
sqlite3 data/sql_app.db .dump > backup.sql

# Import from SQL
sqlite3 data/sql_app.db < backup.sql
```

---

## Git Workflow

### Branching Strategy

```
main (production)
  ├── develop (integration)
  │   ├── feature/add-export-functionality
  │   ├── feature/improve-ocr-accuracy
  │   ├── bugfix/fix-date-filter
  │   └── hotfix/security-patch
```

### Workflow Steps

#### 1. Create Feature Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/document-export

# Or for bugfix
git checkout -b bugfix/fix-mobile-menu
```

#### 2. Make Changes

```bash
# Check status
git status

# Stage changes
git add backend/main.py frontend/src/App.svelte

# Commit with conventional message
git commit -m "feat(backend): add document export to PDF"
```

#### 3. Keep Branch Updated

```bash
# Update from main
git checkout main
git pull origin main
git checkout feature/document-export
git rebase main

# Resolve conflicts if any
git add <conflicted-files>
git rebase --continue
```

#### 4. Push and Create PR

```bash
# Push branch
git push origin feature/document-export

# Create pull request on GitHub
# Include description, tests, and screenshots
```

#### 5. After PR Approval

```bash
# Squash and merge via GitHub UI
# Delete branch
git branch -d feature/document-export
git push origin --delete feature/document-export
```

### Commit Best Practices

```bash
# Good commits
git commit -m "feat(ocr): add support for multi-page PDFs"
git commit -m "fix(frontend): resolve mobile menu z-index issue"
git commit -m "docs: update API documentation with examples"

# Bad commits
git commit -m "changes"
git commit -m "fix stuff"
git commit -m "WIP"
```

### Working with Remotes

```bash
# Add upstream (for forks)
git remote add upstream https://github.com/Sanali209/DocuFlow-.git

# Fetch upstream changes
git fetch upstream

# Merge upstream main
git checkout main
git merge upstream/main
```

---

## Debugging Tips

### Backend Debugging

#### Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.post("/documents/")
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    logger.debug(f"Creating document: {document.dict()}")
    result = crud.create_document(db, document)
    logger.debug(f"Created document with ID: {result.id}")
    return result
```

#### Interactive Debugging with pdb

```python
import pdb

@app.get("/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    pdb.set_trace()  # Debugger will pause here
    document = crud.get_document(db, document_id)
    return document
```

#### VS Code Debugging

**launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "backend.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true
    }
  ]
}
```

#### Database Query Debugging

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    print("SQL:", statement)
    print("Params:", params)
```

### Frontend Debugging

#### Browser DevTools

```javascript
// Debug reactive state
$inspect(documentList);

// Log API calls
async function fetchDocuments() {
  console.log('Fetching documents...');
  const response = await fetch(`${API_URL}/documents/`);
  const data = await response.json();
  console.log('Received:', data);
  return data;
}
```

#### Network Debugging

```javascript
// Intercept fetch requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
  console.log('Fetch:', args);
  return originalFetch.apply(this, args).then(response => {
    console.log('Response:', response);
    return response;
  });
};
```

#### Svelte DevTools

Install [Svelte DevTools](https://github.com/sveltejs/svelte-devtools) browser extension for:
- Component inspection
- State visualization
- Performance profiling

### Docker Debugging

```bash
# Check container logs
docker logs docuflow-app

# Follow logs in real-time
docker logs -f docuflow-app

# Execute commands in container
docker exec -it docuflow-app bash

# Check container resource usage
docker stats docuflow-app

# Inspect container details
docker inspect docuflow-app
```

---

## Common Development Tasks

### Adding a New API Endpoint

1. **Define the route in main.py:**

```python
@app.post("/documents/{document_id}/archive")
def archive_document(document_id: int, db: Session = Depends(get_db)):
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document.status = "Archived"
    db.commit()
    return document
```

2. **Add CRUD function in crud.py (if complex):**

```python
def archive_document(db: Session, document_id: int) -> Optional[models.Document]:
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if document:
        document.status = "Archived"
        document.archived_at = datetime.utcnow()
        db.commit()
        db.refresh(document)
    return document
```

3. **Update schema if needed in schemas.py:**

```python
class DocumentArchive(BaseModel):
    archived_at: datetime
    archived_by: str
```

4. **Add tests:**

```python
def test_archive_document(client):
    # Create document
    response = client.post("/documents/", json={"name": "Test"})
    doc_id = response.json()["id"]
    
    # Archive it
    response = client.post(f"/documents/{doc_id}/archive")
    assert response.status_code == 200
    assert response.json()["status"] == "Archived"
```

5. **Test manually:**

```bash
curl -X POST http://localhost:8000/documents/1/archive
```

### Adding a New Frontend Component

1. **Create component file:**

```svelte
<!-- src/components/ArchiveButton.svelte -->
<script>
  export let documentId;
  export let onArchived = () => {};
  
  let loading = $state(false);
  
  async function archiveDocument() {
    loading = true;
    try {
      const response = await fetch(`/documents/${documentId}/archive`, {
        method: 'POST',
      });
      if (response.ok) {
        onArchived();
      }
    } finally {
      loading = false;
    }
  }
</script>

<button onclick={archiveDocument} disabled={loading}>
  {loading ? 'Archiving...' : 'Archive'}
</button>

<style>
  button {
    padding: 0.5rem 1rem;
    background: #f44336;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
```

2. **Import and use in parent component:**

```svelte
<script>
  import ArchiveButton from './components/ArchiveButton.svelte';
  
  function handleArchived() {
    // Refresh document list
    fetchDocuments();
  }
</script>

<ArchiveButton documentId={doc.id} onArchived={handleArchived} />
```

### Running Production Build Locally

```bash
# Build frontend
cd frontend
npm run build

# Frontend build is in frontend/dist/
# Copy to static directory
rm -rf ../static/*
cp -r dist/* ../static/

# Run backend (serves static files)
cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Access at http://localhost:8000
```

### Database Query Optimization

```python
# Bad: N+1 query problem
documents = db.query(models.Document).all()
for doc in documents:
    tasks = doc.tasks  # Separate query for each document!

# Good: Eager loading
from sqlalchemy.orm import joinedload

documents = db.query(models.Document).options(
    joinedload(models.Document.tasks),
    joinedload(models.Document.tags),
    joinedload(models.Document.notes)
).all()
```

### Adding Environment Variables

1. **Define in backend:**

```python
# backend/main.py
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10MB default
```

2. **Document in wiki:**

Update `Deployment-Guide.md` with new variable.

3. **Add to docker-compose.yml:**

```yaml
environment:
  - MAX_UPLOAD_SIZE=52428800  # 50MB
```

### Code Review Checklist

Before submitting PR:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No console.log or debug statements
- [ ] Error handling implemented
- [ ] Type hints added (Python)
- [ ] Commit messages follow convention
- [ ] No sensitive data in code
- [ ] Performance impact considered

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Svelte 5 Documentation](https://svelte.dev/docs/svelte/overview)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)

---

[← Back to Wiki Home](Home.md) | [Next: API Documentation →](API-Documentation.md)
