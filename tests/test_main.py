import pytest
pytest.importorskip("dishka")

from fastapi.testclient import TestClient

from docuflow.main import app


def test_read_main() -> None:
    # Use context manager to trigger FastAPI lifespan events (SDK initialization)
    with TestClient(app) as client:
        # NiceGUI app might not return JSON for "/" as it's a UI page.
        # We just check if the app starts.
        response = client.get("/")
        assert response.status_code == 200


def test_health_check() -> None:
    # Health check is a regular FastAPI route
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
