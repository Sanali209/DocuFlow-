import pytest

pytest.importorskip("dishka")

from fastapi.testclient import TestClient

from docuflow.main import app


def test_api_endpoints() -> None:
    # Use context manager to trigger FastAPI lifespan events (SDK initialization)
    # Merged to avoid 'threads can only be started once' error from Watchdog/SDK
    with TestClient(app) as client:
        # 1. Main page
        response = client.get("/")
        assert response.status_code == 200

        # 2. Health check
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
