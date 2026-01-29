# Contributing to DocuFlow

Thank you for your interest in contributing to DocuFlow! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Development Workflow](#development-workflow)
4. [Pull Request Process](#pull-request-process)
5. [Code Style Requirements](#code-style-requirements)
6. [Testing Requirements](#testing-requirements)
7. [Documentation Standards](#documentation-standards)
8. [Community Guidelines](#community-guidelines)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender, gender identity and expression, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Our Standards

**Positive behaviors include:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members
- Providing and gracefully receiving constructive feedback

**Unacceptable behaviors include:**
- Use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without permission
- Conduct which could reasonably be considered inappropriate in a professional setting

### Enforcement

Project maintainers are responsible for clarifying standards and will take appropriate and fair corrective action in response to behavior violations.

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the project team. All complaints will be reviewed and investigated promptly and fairly.

---

## How to Contribute

There are many ways to contribute to DocuFlow:

### 1. Report Bugs

Found a bug? Help us improve by reporting it!

**Before submitting:**
- Check if the issue already exists in [GitHub Issues](https://github.com/Sanali209/DocuFlow-/issues)
- Verify the bug in the latest version
- Collect information about your environment

**When reporting, include:**
- Clear, descriptive title
- Detailed description of the issue
- Steps to reproduce the behavior
- Expected behavior vs actual behavior
- Screenshots or videos (if applicable)
- Environment details:
  ```
  - OS: [e.g., Ubuntu 22.04, macOS 13.0, Windows 11]
  - Python version: [e.g., 3.12.0]
  - Node.js version: [e.g., 22.0.0]
  - Docker version: [e.g., 24.0.0]
  - Browser: [e.g., Chrome 120, Firefox 121]
  ```
- Relevant log output or error messages

**Example issue:**
```markdown
**Bug Description**
OCR processing fails for multi-page PDFs larger than 10MB

**Steps to Reproduce**
1. Go to document creation
2. Click "Scan Document"
3. Upload a 15MB PDF with 20 pages
4. Click "Scan"

**Expected Behavior**
Document should be processed and text extracted

**Actual Behavior**
Error message: "Connection timeout"

**Environment**
- OS: Ubuntu 22.04
- Python: 3.12.0
- Docker: 24.0.0
- OCR Service: Hugging Face Spaces (CPU)

**Additional Context**
Smaller PDFs (<5MB) work fine
```

### 2. Suggest Features

Have an idea for a new feature?

**Before suggesting:**
- Check if it's already suggested or implemented
- Consider if it aligns with DocuFlow's goals
- Think about implementation complexity

**Feature request template:**
```markdown
**Feature Description**
Brief description of the feature

**Problem it Solves**
What problem does this solve?

**Proposed Solution**
How would you implement this?

**Alternatives Considered**
What other solutions did you consider?

**Additional Context**
Screenshots, mockups, or examples
```

### 3. Improve Documentation

Documentation improvements are always welcome!

**Areas to contribute:**
- Fix typos or unclear explanations
- Add examples or tutorials
- Improve API documentation
- Translate documentation
- Create video tutorials
- Write blog posts about DocuFlow

### 4. Write Code

Contribute code by fixing bugs or implementing features!

See [Development Workflow](#development-workflow) for details.

### 5. Review Pull Requests

Help review pull requests from other contributors:
- Test the changes
- Review code quality
- Provide constructive feedback
- Check documentation updates

### 6. Help Others

Help other users in:
- GitHub Issues
- GitHub Discussions
- Stack Overflow
- Community forums

---

## Development Workflow

### Step 1: Set Up Development Environment

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/DocuFlow-.git
cd DocuFlow-

# Add upstream remote
git remote add upstream https://github.com/Sanali209/DocuFlow-.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# Install development tools
pip install pytest pytest-cov black flake8 mypy
```

### Step 2: Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bugfix
git checkout -b bugfix/issue-number-description
```

**Branch naming conventions:**
- `feature/` - New features (e.g., `feature/export-to-pdf`)
- `bugfix/` - Bug fixes (e.g., `bugfix/123-fix-date-filter`)
- `docs/` - Documentation changes (e.g., `docs/update-api-guide`)
- `refactor/` - Code refactoring (e.g., `refactor/optimize-queries`)
- `test/` - Test additions (e.g., `test/add-attachment-tests`)

### Step 3: Make Changes

**Write clean, focused code:**
- Make one logical change per commit
- Follow code style guidelines (see below)
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and focused

**Test your changes:**
```bash
# Backend tests
cd backend
pytest

# Manual testing
uvicorn backend.main:app --reload

# Frontend testing
cd frontend
npm run dev
```

### Step 4: Commit Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Stage changes
git add backend/main.py

# Commit with conventional message
git commit -m "feat(backend): add document export to PDF"

# More examples
git commit -m "fix(frontend): resolve mobile menu navigation issue"
git commit -m "docs: update deployment guide with Heroku instructions"
git commit -m "test(backend): add tests for attachment endpoints"
git commit -m "refactor(ocr): optimize image preprocessing"
```

**Commit message format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, no logic change)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `perf` - Performance improvements

**Scope examples:**
- `backend` - Backend changes
- `frontend` - Frontend changes
- `ocr` - OCR service changes
- `db` - Database changes
- `api` - API changes

### Step 5: Push Changes

```bash
# Push to your fork
git push origin feature/your-feature-name
```

### Step 6: Create Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template (see below)
5. Submit the pull request

---

## Pull Request Process

### PR Title

Use conventional commit format:
```
feat(backend): add bulk document export functionality
```

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Related Issues
Closes #123
Related to #456

## Changes Made
- Added PDF export functionality
- Updated document schema
- Added export button to UI
- Added tests for export

## Testing Performed
- [ ] Tested locally
- [ ] Added/updated unit tests
- [ ] All tests pass
- [ ] Tested on mobile devices
- [ ] Tested in multiple browsers

### Test Details
Tested with:
- 100 documents successfully exported
- Large documents (50+ pages) work correctly
- Export includes all metadata
- Browser tested: Chrome 120, Firefox 121

## Screenshots (if applicable)
[Add screenshots here]

## Checklist
- [ ] My code follows the project's code style
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged

## Additional Notes
Any additional information reviewers should know.
```

### Review Process

1. **Automated Checks**: CI/CD will run tests automatically
2. **Code Review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, maintainers will merge

**During review:**
- Be responsive to feedback
- Make requested changes promptly
- Keep discussions professional and constructive
- Update your PR as needed

**Making changes after review:**
```bash
# Make changes
git add .
git commit -m "refactor: address review feedback"
git push origin feature/your-feature-name
```

### Merging

Once approved, maintainers will:
- Squash and merge (most common)
- Merge commit (for larger features)
- Rebase and merge (for clean history)

After merge:
```bash
# Update your local main
git checkout main
git pull upstream main

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

---

## Code Style Requirements

### Python (Backend)

#### PEP 8 Compliance

```bash
# Check code style
flake8 backend/ --max-line-length=100

# Auto-format with Black
black backend/

# Type checking
mypy backend/
```

#### Type Hints

Always use type hints:
```python
# Good
def get_document(db: Session, document_id: int) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.id == document_id).first()

# Bad
def get_document(db, document_id):
    return db.query(models.Document).filter(models.Document.id == document_id).first()
```

#### Docstrings

Use Google-style docstrings:
```python
def create_document(db: Session, document: schemas.DocumentCreate) -> models.Document:
    """
    Create a new document in the database.
    
    Args:
        db: Database session
        document: Document creation schema
        
    Returns:
        The created document object
        
    Raises:
        ValueError: If document data is invalid
    """
    db_document = models.Document(**document.dict())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document
```

#### Error Handling

```python
# Good - Specific exceptions with context
@app.get("/documents/{document_id}")
def read_document(document_id: int, db: Session = Depends(get_db)):
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document with id {document_id} not found"
        )
    return document

# Bad - Generic errors
@app.get("/documents/{document_id}")
def read_document(document_id: int, db: Session = Depends(get_db)):
    try:
        return crud.get_document(db, document_id)
    except:
        return {"error": "Something went wrong"}
```

### JavaScript/Svelte (Frontend)

#### Prettier Formatting

```bash
# Format code
cd frontend
npm run format

# Check formatting
npm run format:check
```

#### ESLint

```bash
# Lint code
npm run lint

# Fix auto-fixable issues
npm run lint:fix
```

#### Component Style

```svelte
<script>
  // 1. Imports
  import { onMount } from 'svelte';
  import DocumentCard from './DocumentCard.svelte';
  
  // 2. Props
  export let title = 'Default Title';
  export let onSave = () => {};
  
  // 3. State (Svelte 5 Runes)
  let documents = $state([]);
  let loading = $state(false);
  
  // 4. Derived state
  let hasDocuments = $derived(documents.length > 0);
  
  // 5. Functions
  async function fetchDocuments() {
    loading = true;
    try {
      const response = await fetch('/api/documents');
      documents = await response.json();
    } finally {
      loading = false;
    }
  }
  
  // 6. Lifecycle
  onMount(() => {
    fetchDocuments();
  });
</script>

<div class="container">
  <h1>{title}</h1>
  
  {#if loading}
    <p>Loading...</p>
  {:else if hasDocuments}
    {#each documents as doc}
      <DocumentCard document={doc} />
    {/each}
  {:else}
    <p>No documents found</p>
  {/if}
</div>

<style>
  .container {
    padding: 1rem;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  h1 {
    font-size: 2rem;
    margin-bottom: 1rem;
  }
</style>
```

### Code Comments

```python
# Good - Comments explain WHY, not WHAT
# Use regex to extract document name from OCR text
# Format: "Order: <name> Date: <date>"
match = re.search(doc_name_regex, ocr_text)

# Bad - Comments state the obvious
# Search for pattern in text
match = re.search(doc_name_regex, ocr_text)
```

---

## Testing Requirements

### Backend Tests

**Required for all PRs that change backend logic:**

```python
# test_your_feature.py
import pytest
from fastapi.testclient import TestClient

def test_your_feature(client):
    """Test description."""
    response = client.post("/endpoint", json={"data": "value"})
    assert response.status_code == 200
    assert response.json()["field"] == "expected"
```

**Run tests before submitting:**
```bash
cd backend
pytest
pytest --cov=. --cov-report=html  # With coverage
```

**Coverage requirements:**
- New features: 80%+ coverage
- Bug fixes: Add test reproducing the bug
- Critical paths: 100% coverage

### Frontend Tests

While not strictly required, frontend tests are appreciated:

```javascript
// MyComponent.test.js
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import MyComponent from './MyComponent.svelte';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(MyComponent, { props: { title: 'Test' } });
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### Manual Testing

Always manually test your changes:

1. **Functionality**: Feature works as intended
2. **Edge cases**: Handle invalid input, errors
3. **UI/UX**: Visual appearance, responsiveness
4. **Performance**: No significant slowdowns
5. **Browser compatibility**: Test in multiple browsers
6. **Mobile**: Test on mobile devices

**Testing checklist:**
- [ ] Feature works in development mode
- [ ] Feature works in production build
- [ ] No console errors or warnings
- [ ] Responsive on mobile
- [ ] Works in Chrome, Firefox, Safari
- [ ] Handles errors gracefully
- [ ] Performance is acceptable

---

## Documentation Standards

### Code Documentation

**When to document:**
- Public APIs and endpoints
- Complex algorithms or logic
- Non-obvious design decisions
- Configuration options
- Function parameters and return values

**What NOT to document:**
- Obvious code (`i++` doesn't need a comment)
- Temporary code (use `TODO:` instead)
- Outdated information (keep docs up to date!)

### README and Wiki

**Update documentation when you:**
- Add new features
- Change existing functionality
- Add configuration options
- Change API endpoints
- Fix significant bugs

**Documentation locations:**
- `README.md` - Project overview and quick start
- `wiki/` - Detailed guides and tutorials
- `backend/` docstrings - API documentation
- Code comments - Implementation details

### API Documentation

FastAPI auto-generates API docs, but enhance with examples:

```python
@app.post("/documents/", response_model=schemas.Document)
def create_document(
    document: schemas.DocumentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new document.
    
    **Example request:**
    ```json
    {
      "name": "Quarterly Report",
      "type": "Report",
      "status": "In Progress",
      "author": "John Doe",
      "description": "Q4 2024 financial report"
    }
    ```
    
    **Returns:**
    Document object with generated ID and timestamps.
    """
    return crud.create_document(db=db, document=document)
```

---

## Community Guidelines

### Communication

**Be respectful and professional:**
- Use welcoming, inclusive language
- Provide constructive feedback
- Accept criticism gracefully
- Focus on the issue, not the person

**Examples:**

**Good:**
```
This approach might have performance issues with large datasets. 
Have you considered using pagination or lazy loading?
```

**Bad:**
```
This code is terrible and will never work.
```

### Response Times

**Contributors:**
- Respond to review feedback within a week
- Update your PR if inactive for 2 weeks or it may be closed
- Communicate if you need more time

**Maintainers:**
- First response to issues within 1 week
- PR reviews within 2 weeks
- May take longer during busy periods

### Conflict Resolution

If disagreements arise:
1. Stay calm and professional
2. Focus on technical merits
3. Seek compromise
4. Escalate to maintainers if needed
5. Accept maintainer decisions as final

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README
- GitHub contributor graph

Thank you for contributing to DocuFlow! 🎉

---

## Questions?

- **General questions**: [GitHub Discussions](https://github.com/Sanali209/DocuFlow-/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/Sanali209/DocuFlow-/issues)
- **Security issues**: Email maintainers privately (see `SECURITY.md`)

---

## License

By contributing to DocuFlow, you agree that your contributions will be licensed under the MIT License.

---

## Additional Resources

- [Developer Guide](Developer-Guide.md) - Development setup and workflow
- [API Documentation](API-Documentation.md) - API reference
- [Deployment Guide](Deployment-Guide.md) - Deployment instructions
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8](https://peps.python.org/pep-0008/) - Python style guide
- [Svelte Documentation](https://svelte.dev/)

---

[← Back to Wiki Home](Home.md) | [Get Started Contributing →](Developer-Guide.md)
