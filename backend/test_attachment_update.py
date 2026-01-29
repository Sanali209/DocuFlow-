"""Test for updating documents with attachments."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from backend.main import app, get_db
from backend.database import Base

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_attachment.db"
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
    os.makedirs("static/uploads", exist_ok=True)

def teardown_module(module):
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_attachment.db"):
        os.remove("test_attachment.db")
    # Clean up test attachment files
    test_files = ["test_attachment.txt", "file1.txt", "file2.txt", "file3.txt"]
    for filename in test_files:
        file_path = f"static/uploads/{filename}"
        if os.path.exists(file_path):
            os.remove(file_path)

def test_update_document_with_attachments():
    """Test updating a document with new attachments."""
    # Create a document first
    doc_data = {
        "name": "Test Document",
        "type": "plan",
        "status": "in_progress",
        "content": "Initial content"
    }
    response = client.post("/documents/", json=doc_data)
    assert response.status_code == 200
    doc = response.json()
    doc_id = doc["id"]
    
    # Mock upload file first
    filename = "test_attachment.txt"
    file_path = f"static/uploads/{filename}"
    with open(file_path, "w") as f:
        f.write("test attachment content")
    
    # Update document with attachments
    update_data = {
        "name": "Updated Document",
        "content": "Updated content",
        "attachments": [{
            "filename": filename,
            "file_path": f"/uploads/{filename}",
            "media_type": "text/plain"
        }]
    }
    
    response = client.put(f"/documents/{doc_id}", json=update_data)
    assert response.status_code == 200
    
    updated_doc = response.json()
    assert updated_doc["name"] == "Updated Document"
    assert updated_doc["content"] == "Updated content"
    assert len(updated_doc["attachments"]) == 1
    assert updated_doc["attachments"][0]["filename"] == filename
    
    # Verify document was updated correctly
    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    fetched_doc = response.json()
    assert fetched_doc["name"] == "Updated Document"
    assert len(fetched_doc["attachments"]) == 1

def test_create_document_with_invalid_attachments():
    """Test that creating a document with invalid attachment data fails gracefully."""
    # Create a document with missing required fields in attachment
    doc_data = {
        "name": "Test Document",
        "type": "plan",
        "status": "in_progress",
        "attachments": [{
            # Missing required fields: filename, file_path, media_type
        }]
    }
    response = client.post("/documents/", json=doc_data)
    # Should return 422 for validation error
    assert response.status_code == 422

def test_update_with_multiple_attachments():
    """Test updating a document with multiple new attachments."""
    # Create a document
    doc_data = {
        "name": "Multi-Attach Doc",
        "type": "plan",
        "status": "in_progress"
    }
    response = client.post("/documents/", json=doc_data)
    doc_id = response.json()["id"]
    
    # Create mock files
    files = ["file1.txt", "file2.txt", "file3.txt"]
    for f in files:
        file_path = f"static/uploads/{f}"
        with open(file_path, "w") as fp:
            fp.write(f"content of {f}")
    
    # Update with multiple attachments
    update_data = {
        "attachments": [
            {
                "filename": f,
                "file_path": f"/uploads/{f}",
                "media_type": "text/plain"
            }
            for f in files
        ]
    }
    
    response = client.put(f"/documents/{doc_id}", json=update_data)
    assert response.status_code == 200
    
    updated_doc = response.json()
    assert len(updated_doc["attachments"]) == 3
    
    # Verify all attachments are present
    attachment_filenames = [att["filename"] for att in updated_doc["attachments"]]
    for f in files:
        assert f in attachment_filenames
