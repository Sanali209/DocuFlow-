# API Reference

DocuFlow's API is built with **FastAPI**, which automatically generates interactive API documentation.

## Viewing the Documentation

1.  Start the backend: `python main.py`
2.  Open your browser to:
    *   **Swagger UI**: `http://localhost:8000/docs`
    *   **ReDoc**: `http://localhost:8000/redoc`

## Key Endpoints

### Documents
*   `GET /api/documents`: List documents (Orders).
*   `GET /api/documents/{id}/gnc`: Get parsed GNC data for a specific file.

### Sync
*   `POST /api/sync/trigger`: Manual trigger for network synchronization.

### Settings
*   `GET /api/settings`: Retrieve application configuration.
