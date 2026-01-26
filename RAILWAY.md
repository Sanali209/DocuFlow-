# Railway Deployment

This repository is set up for deployment on Railway as a monorepo.

## Instructions

1.  **Create a Project on Railway.**
2.  **Add a Service (Backend):**
    *   Connect your GitHub repository.
    *   Go to **Settings** > **Root Directory** and set it to `/backend`.
    *   Railway will automatically detect Python and `requirements.txt`.
    *   The start command is defined in `backend/railway.json` (or `Procfile`).
3.  **Add a Service (Frontend):**
    *   Add another service from the same repository.
    *   Go to **Settings** > **Root Directory** and set it to `/frontend`.
    *   Railway will detect Node.js.
    *   **Environment Variables:**
        *   `VITE_API_URL`: Set this to the public URL of your Backend service (e.g., `https://backend-production.up.railway.app`).
    *   The start command is defined in `frontend/railway.json`.

## Notes
*   The Frontend uses `npm run preview` which serves the build using Vite. For production, consider using a static file server like `serve` or Nginx.
*   The Backend allows all origins by default in `main.py` (or configured via `ALLOWED_ORIGINS` env var).
