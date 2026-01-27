from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, AsyncMock, MagicMock
import pytest

client = TestClient(app)

def test_read_main():
    response = client.get("/documents/")
    assert response.status_code == 200

@patch("httpx.AsyncClient.post")
def test_scan_document(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"markdown": "Order Project Alpha Specs\n\nSome content..."}
    mock_response.raise_for_status.return_value = None

    if not isinstance(mock_post, AsyncMock):
        pass

    mock_post.return_value = mock_response

    files = {'file': ('test.jpg', b'fake image content', 'image/jpeg')}
    response = client.post("/documents/scan", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Project Alpha Specs"
    assert "Some content" in data["content"]

def test_create_and_read_document():
    doc_data = {
        "name": "Test Doc With Content",
        "type": "plan",
        "status": "in_progress",
        "content": "# Markdown Content"
    }
    response = client.post("/documents/", json=doc_data)
    assert response.status_code == 200
    data = response.json()
    doc_id = data["id"]
    assert data["content"] == "# Markdown Content"

    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["content"] == "# Markdown Content"

def test_update_document():
    # Create first
    doc_data = {"name": "To Update", "type": "plan", "status": "in_progress"}
    response = client.post("/documents/", json=doc_data)
    doc_id = response.json()["id"]

    # Update
    update_data = {"name": "Updated Name", "content": "New Content"}
    response = client.put(f"/documents/{doc_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["content"] == "New Content"
