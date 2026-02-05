import sys
import os
import json
sys.path.append(os.getcwd())

from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import Base
from backend.dependencies import get_db
import pytest

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

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_full_nesting_flow(test_db):
    # 1. Create dummy GNC file
    os.makedirs("storage/parts", exist_ok=True)
    gnc_path = "storage/parts/test_part.gnc"
    with open(gnc_path, "w") as f:
        f.write("G21 G90\nG0 X0 Y0\nG1 X100 Y0\nG1 X100 Y100\nG1 X0 Y100\nG1 X0 Y0\nM30")
    
    # 2. Create Material
    client.post("/materials", json={"name": "Aluminum"})
    
    # 3. Create Part with GNC path
    part_res = client.post("/parts", json={
        "name": "Nesting Part",
        "registration_number": "NP-001",
        "material_id": 1,
        "width": 100,
        "height": 100,
        "gnc_file_path": gnc_path
    })
    part_id = part_res.json()["id"]

    # 4. Create Order
    order_data = {
        "name": "Nesting Order",
        "parts": [
            {"id": part_id, "qty": 2}
        ]
    }
    
    response = client.post("/documents/order", json=order_data)
    assert response.status_code == 200
    doc_id = response.json()["id"]
    
    # 5. Verify Tasks and Associations
    tasks_res = client.get(f"/documents/{doc_id}/tasks")
    tasks = tasks_res.json()
    assert len(tasks) == 2
    task1 = tasks[0]
    
    # Check if part_associations is returned (if schema includes it)
    # If not, we might need to check DB directly or update Schema
    # Let's check GNC endpoint directly using part_id
    
    # 6. Fetch Part GNC
    gnc_res = client.get(f"/parts/{part_id}/gnc")
    assert gnc_res.status_code == 200
    sheet = gnc_res.json()
    assert sheet["program_width"] > 0
    
    # Cleanup
    if os.path.exists(gnc_path):
        os.remove(gnc_path)
