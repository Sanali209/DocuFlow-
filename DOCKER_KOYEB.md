# Docker / Koyeb Deployment

This repository is configured for deployment as a **Monolith** (Single Service) on container-based platforms like **Koyeb**, **Render**, **Railway**, or vanilla **Docker**.

The application uses a single Dockerfile in the root directory that performs a multi-stage build:
1.  **Frontend Build Stage:** Builds the Svelte frontend using Node.js.
2.  **Runtime Stage:** Sets up the Python FastAPI backend and serves the frontend static files from the `/static` directory.

## Deploying on Koyeb

1.  **Create an Account** on [Koyeb](https://www.koyeb.com/).
2.  **Create a New App/Service:**
    *   Select **GitHub** as the source.
    *   Choose this repository.
    *   **Builder:** Dockerfile.
    *   **Dockerfile Location:** `Dockerfile` (default, root directory).
    *   **Privileged:** No.
    *   **Ports:** 8000 (The application listens on port 8000 by default, or the port specified by `$PORT`).
    *   **Environment Variables:**
        *   `OCR_SERVICE_URL`: URL of the OCR service (optional, defaults to `http://localhost:7860` or can be configured in App Settings).
        *   `ALLOWED_ORIGINS`: Comma-separated list of allowed origins (e.g. `https://your-app.koyeb.app`).
    *   **Deploy.**

The application will be available at your Koyeb public URL (e.g., `https://your-app-xyz.koyeb.app`). The frontend is served automatically by the backend.

## Running with Docker (Local)

To build and run the image locally:

```bash
# Build the image
docker build -t doc-tracker .

# Run the container
docker run -p 8000:8000 doc-tracker
```

Access the application at `http://localhost:8000`.

## Running with Docker Compose

```bash
docker-compose up --build
```
