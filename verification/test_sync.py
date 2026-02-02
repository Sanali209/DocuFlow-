import sys
import os
import time
import shutil
import logging

# Ensure root is in path
sys.path.append(os.getcwd())

from backend import models, crud, database
from backend.sync_service import SyncService
from sqlalchemy.orm import Session

# VALID LOGGING CONFIG
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.sync_service")
logger.setLevel(logging.INFO)

def setup_test_env():
    # Clean DB entries
    db_temp = database.SessionLocal()
    db_temp.query(models.Attachment).filter(models.Attachment.file_path.like("%testing%")).delete(synchronize_session=False)
    db_temp.query(models.Document).filter(models.Document.name.in_(["TEST_PART_A", "Order_123", "OrderFile_801"])).delete(synchronize_session=False)
    db_temp.query(models.Part).filter(models.Part.name.in_(["TEST_PART_A.gnc", "OrderFile_801.gnc"])).delete(synchronize_session=False)
    db_temp.commit()
    db_temp.close()
    
    shutil.rmtree("testing/mihtav_test", ignore_errors=True)
    shutil.rmtree("testing/sidra_test", ignore_errors=True)
    os.makedirs("testing/mihtav_test", exist_ok=True)
    os.makedirs("testing/sidra_test", exist_ok=True)

def create_dummy_gnc(path, filename, content=""):
    with open(os.path.join(path, filename), "w") as f:
        f.write(content if content else "%") # Default to machine-like start

def test_sync():
    print("Setting up test environment...")
    setup_test_env()
    
    db = database.SessionLocal()
    
    # 1. Configure Paths
    print("Configuring settings...")
    mihtav_path = os.path.abspath("testing/mihtav_test")
    sidra_path = os.path.abspath("testing/sidra_test")
    crud.set_setting(db, "sync_mihtav_path", mihtav_path)
    crud.set_setting(db, "sync_sidra_path", sidra_path)
    
    # 2. Create Dummy Files
    print("Creating dummy files...")
    # Sidra File (Part)
    create_dummy_gnc(sidra_path, "TEST_PART_A.gnc", "(PART NAME: Test Part)\nG01 X10 Y10")
    # Mihtav File (Order)
    # Put in a subfolder "Order_123"
    order_dir = os.path.join(mihtav_path, "Order_123")
    os.makedirs(order_dir, exist_ok=True)
    create_dummy_gnc(order_dir, "OrderFile_801.gnc", "*N1145 P660=190,P150=1,P151=1\n(PART NAME: Order Part)")
    
    # 3. Run Sync
    print("Running Sync Service cycle...")
    service = SyncService()
    try:
        service._sync_cycle()
    except Exception as e:
        print(f"Sync failed: {e}")
        import traceback
        traceback.print_exc()
        
    # 4. Verify Results
    print("Verifying results...")
    
    # Check Part from Sidra
    part = db.query(models.Part).filter(models.Part.name == "TEST_PART_A.gnc").first()
    if part:
        print(f"[PASS] Part created: {part.name}")
        # Verify linked Document
        doc = db.query(models.Document).filter(models.Document.content.like(f"%{part.name}%")).first()
        doc_part = db.query(models.Document).filter(models.Document.name == "TEST_PART_A").first()
        if doc_part:
             print(f"[PASS] Document created for Part: {doc_part.name}, Status: {doc_part.status}")
        else:
             print(f"[FAIL] Document for Part not found")
    else:
        print(f"[FAIL] Part NOT created")
        
    # Check Order from Mihtav
    order_doc = db.query(models.Document).filter(models.Document.name == "Order_123").first()
    if order_doc:
        print(f"[PASS] Order Document created: {order_doc.name}")
        if "Machine Edit" in (order_doc.description or ""):
            print(f"[PASS] 801 Detection worked: {order_doc.description}")
        else:
            print(f"[FAIL] 801 Detection failed. Desc: {order_doc.description}")
            
        part_order = db.query(models.Part).filter(models.Part.name == "OrderFile_801.gnc").first()
        if part_order:
             print(f"[PASS] Part extracted from Order: {part_order.name}")
        else:
             print(f"[FAIL] Part extraction from Order failed")

    else:
        print(f"[FAIL] Order Document NOT created")

    db.close()
    
if __name__ == "__main__":
    test_sync()
