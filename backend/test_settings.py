from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, AsyncMock, MagicMock
import pytest

client = TestClient(app)

def test_settings_flow():
    # Read default
    response = client.get("/settings/ocr_url")
    assert response.status_code == 200
    assert response.json()["value"] == "http://localhost:7860"

    # Update
    new_url = "http://my-custom-ocr.com"
    response = client.put("/settings/", json={"key": "ocr_url", "value": new_url})
    assert response.status_code == 200
    assert response.json()["value"] == new_url

    # Read updated
    response = client.get("/settings/ocr_url")
    assert response.status_code == 200
    assert response.json()["value"] == new_url

@patch("httpx.AsyncClient.post")
def test_scan_uses_db_setting(mock_post):
    # Set custom URL
    custom_url = "http://custom-ocr.com"
    client.put("/settings/", json={"key": "ocr_url", "value": custom_url})

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"markdown": "Order Custom Specs"}
    mock_response.raise_for_status.return_value = None

    if not isinstance(mock_post, AsyncMock):
        pass

    mock_post.return_value = mock_response

    files = {'file': ('test.jpg', b'content', 'image/jpeg')}
    client.post("/documents/scan", files=files)

    # Verify call used the custom URL
    args, _ = mock_post.call_args
    assert args[0].startswith(custom_url)
