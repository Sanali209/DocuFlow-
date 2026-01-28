from fastapi.testclient import TestClient
from backend.main import app
from datetime import date

client = TestClient(app)

def test_create_and_read_journal_entry():
    # Create Document first
    doc_response = client.post("/documents/", json={
        "name": "Journal Doc",
        "type": "plan",
        "status": "in_progress"
    })
    doc_id = doc_response.json()["id"]

    # Create Entry
    entry_data = {
        "text": "Initial Entry",
        "type": "info",
        "status": "in_progress",
        "document_id": doc_id,
        "author": "Tester"
    }
    response = client.post("/journal/", json=entry_data)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Initial Entry"
    assert data["status"] == "in_progress"
    assert data["document_id"] == doc_id

    entry_id = data["id"]

    # Read
    response = client.get("/journal/")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) > 0
    # Check if entry is present (DB might be shared/dirty)
    assert any(e["id"] == entry_id for e in entries)

def test_update_status():
    # Create Entry
    entry_data = {"text": "To Update", "type": "warning", "status": "in_progress"}
    response = client.post("/journal/", json=entry_data)
    entry_id = response.json()["id"]

    # Update to Done
    update_data = {"status": "done"}
    response = client.put(f"/journal/{entry_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["status"] == "done"

def test_filter_by_date():
    today = date.today().isoformat()

    # Create Entry today
    client.post("/journal/", json={"text": "Today's Entry", "type": "info", "status": "in_progress"})

    # Filter by today
    response = client.get(f"/journal/?date={today}")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) > 0
    assert entries[0]["created_at"] == today

    # Filter by future date
    response = client.get("/journal/?date=2099-01-01")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 0

def test_filter_by_document():
    # Create Doc 1 & Entry
    doc1 = client.post("/documents/", json={"name": "Doc 1", "type": "other", "status": "in_progress"}).json()
    client.post("/journal/", json={"text": "Entry 1", "type": "info", "status": "in_progress", "document_id": doc1["id"]})

    # Create Doc 2 & Entry
    doc2 = client.post("/documents/", json={"name": "Doc 2", "type": "other", "status": "in_progress"}).json()
    client.post("/journal/", json={"text": "Entry 2", "type": "info", "status": "in_progress", "document_id": doc2["id"]})

    # Filter by Doc 1
    response = client.get(f"/journal/?document_id={doc1['id']}")
    assert response.status_code == 200
    entries = response.json()
    # Should contain Entry 1 but not Entry 2
    ids = [e["document_id"] for e in entries]
    assert doc1["id"] in ids
    assert doc2["id"] not in ids
