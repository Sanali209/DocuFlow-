from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import shutil

from backend.main import app, get_db
from backend.database import Base
from backend import models

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_module(module):
    Base.metadata.create_all(bind=engine)
    # Ensure static/uploads exists
    os.makedirs("static/uploads", exist_ok=True)

def teardown_module(module):
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")
    # Clean up uploads
    # if os.path.exists("static/uploads"):
    #     shutil.rmtree("static/uploads")

def test_assignee_filtering():
    # Create doc
    response = client.post("/documents/", json={"name": "Doc 1", "type": "plan", "status": "in_progress"})
    assert response.status_code == 200
    doc_id = response.json()["id"]

    # Create task with assignee "Alice"
    client.post(f"/documents/{doc_id}/tasks", json={"name": "Task 1", "assignee": "Alice"})
    # Create task with assignee "Bob"
    client.post(f"/documents/{doc_id}/tasks", json={"name": "Task 2", "assignee": "Bob"})

    # Filter by Alice
    response = client.get(f"/documents/?assignee=Alice")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id

    # Filter by Bob
    response = client.get(f"/documents/?assignee=Bob")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1

    # Filter by Charlie (non-existent)
    response = client.get(f"/documents/?assignee=Charlie")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 0

def test_journal_visibility():
    # Create doc
    response = client.post("/documents/", json={"name": "Doc Journal", "type": "plan", "status": "in_progress"})
    doc_id = response.json()["id"]

    # Create journal entry linked to doc
    response = client.post("/journal/", json={
        "text": "Linked Note",
        "type": "info",
        "status": "pending",
        "document_id": doc_id
    })
    assert response.status_code == 200
    entry_id = response.json()["id"]

    # Fetch all journal entries (simulate Journal View)
    response = client.get("/journal/")
    assert response.status_code == 200
    entries = response.json()

    found = False
    for e in entries:
        if e["id"] == entry_id:
            found = True
            break
    assert found, "Document-linked journal entry not found in general list"

def test_file_cleanup():
    # Mock upload file
    filename = "test_cleanup.txt"
    file_path = f"static/uploads/{filename}"
    with open(file_path, "w") as f:
        f.write("dummy content")

    # Create doc with attachment
    response = client.post("/documents/", json={
        "name": "Doc Cleanup",
        "type": "other",
        "status": "in_progress",
        "attachments": [{
            "filename": filename,
            "file_path": f"/uploads/{filename}",
            "media_type": "text/plain"
        }]
    })
    doc_id = response.json()["id"]

    # Verify file exists
    assert os.path.exists(file_path)

    # Delete document
    response = client.delete(f"/documents/{doc_id}")
    assert response.status_code == 200

    # Verify file is gone
    assert not os.path.exists(file_path), "File was not deleted when document was deleted"
