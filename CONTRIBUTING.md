# Contributing to DocuFlow

We welcome contributions to improve DocuFlow! Because this is a production-critical system for the manufacturing floor, please follow these guidelines to ensure stability and quality.

## Development Environment Setup

### Recommended Extensions (VS Code)
*   **Python**: `ms-python.python`
*   **Svelte for VS Code**: `svelte.svelte-vscode`
*   **ESLint**: `dbaeumer.vscode-eslint`
*   **Ruff**: `charliermarsh.ruff` (for fast Python linting)

### Initial Setup
1.  **Fork & Clone**: Fork the repo and clone it locally.
2.  **Install Dependencies**:
    ```bash
    # Backend
    cd backend
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt

    # Frontend
    cd ../frontend
    npm install
    ```

## Testing

We have specific test suites located in the `testing/` directory (distinct from unit tests).

### Running Tests
```bash
# From root directory
python -m pytest testing/test_fix_scanner.py
python -m pytest testing/test_refactor_scanner.py
```

## Development Workflow

1.  **Create a Branch**: Create a feature branch for your work (`git checkout -b feature/amazing-feature`).
2.  **Code**: Implement your changes.
3.  **Test**: Run existing tests and add new ones if applicable.
4.  **Lint**: Ensure code follows standard styling (Ruff for Python, Prettier for Svelte).
5.  **Commit**: Use descriptive commit messages.
6.  **Pull Request**: Submit a PR to the `main` branch.

## Project Structure

*   `backend/`: FastAPI application, database models, and business logic.
*   `frontend/`: Svelte 5 application (Vite).
*   `testing/`: Integration and scanner logic tests.
*   `build_dist.py`: Script for building the executable.

## Reporting Bugs

If you find a bug, please open an issue describing:
1.  What you tried to do.
2.  What happened (screenshots are helpful).
3.  What you expected to happen.

Happy Coding!
