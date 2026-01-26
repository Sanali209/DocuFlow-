# Docker / Koyeb Deployment

This repository includes Dockerfiles for deploying the application on container-based platforms like **Koyeb**, **Kubernetes**, or vanilla **Docker**.

## Docker Structure

*   `backend/Dockerfile`: Python FastAPI image.
*   `frontend/Dockerfile`: Multi-stage build (Node build -> Nginx serve).
*   `docker-compose.yml`: Orchestration for local development or simple deployment.

## Deploying on Koyeb

1.  **Create an Account** on [Koyeb](https://www.koyeb.com/).
2.  **Deploy Backend:**
    *   Create a new App/Service.
    *   Select **GitHub** as the source.
    *   Choose this repository.
    *   **Builder:** Dockerfile.
    *   **Dockerfile Location:** `backend/Dockerfile`.
    *   **Privileged:** No.
    *   **Ports:** 8000.
    *   Deploy. Copy the public URL (e.g., `https://backend-xyz.koyeb.app`).
3.  **Deploy Frontend:**
    *   Create another Service (in the same App or new one).
    *   Select the same repository.
    *   **Builder:** Dockerfile.
    *   **Dockerfile Location:** `frontend/Dockerfile`.
    *   **Ports:** 80.
    *   **Environment Variables (Build Args):**
        *   Koyeb allows setting Environment Variables. However, for the Frontend build (which needs `VITE_API_URL` at build time), you might need to ensure the variable is available during the build phase.
        *   *Note:* Standard Environment Variables in Koyeb are runtime. To pass build arguments, check Koyeb's advanced settings or use a `koyeb.yaml` if supported.
        *   *Alternative:* If you cannot set build args easily, you can hardcode the URL in `frontend/.env.production` before pushing, or update `api.js` to fallback to a relative path `/api` and configure Nginx to proxy requests to the backend.

## Running with Docker Compose (Local)

```bash
docker-compose up --build
```

Access the frontend at `http://localhost`.
Access the backend at `http://localhost:8000`.
