import os
import shutil
import tempfile
import sys
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scanner import scan_library
from backend import models

def test_scanner_logic():
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Setup mihtav path
        mihtav_path = os.path.normpath(os.path.abspath(os.path.join(temp_dir, "mihtav")))
        os.makedirs(mihtav_path)
        
        # Files in root (should be orders)
        root_file = os.path.join(mihtav_path, "root_order.gnc")
        with open(root_file, 'w') as f: f.write("(PART NAME: ROOT)\n")
        
        # Subfolder (should be order)
        subdir = os.path.join(mihtav_path, "folder_order")
        os.makedirs(subdir)
        sub_file = os.path.join(subdir, "sub_task.gnc")
        with open(sub_file, 'w') as f: f.write("(PART NAME: SUB)\n")
        
        # Deduplication test: base + _801
        dedupe_base = os.path.join(subdir, "dedupe.gnc")
        dedupe_801 = os.path.join(subdir, "dedupe_801.gnc")
        dedupe_to801 = os.path.join(subdir, "dedupe_to801.gnc")
        with open(dedupe_base, 'w') as f: f.write("(PART NAME: BASE)\n")
        with open(dedupe_801, 'w') as f: f.write("(PART NAME: 801)\n")
        with open(dedupe_to801, 'w') as f: f.write("(PART NAME: TO801)\n")

        # 2. Mock DB
        db = MagicMock()
        
        # Mock database queries to handle document lookup (for cache logic)
        def mock_query(model):
            query = MagicMock()
            query.filter.return_value = query
            query.first.return_value = None # Always simulate new doc/task
            return query
        db.query.side_effect = mock_query

        # Mock crud.get_setting
        from backend import crud
        crud_mock = MagicMock()
        crud.get_setting = crud_mock
        
        def mock_get_setting(db, key):
            if key == "sync_mihtav_path":
                return MagicMock(value=mihtav_path)
            if key == "sync_sidra_path":
                return MagicMock(value=None)
            return None
        crud_mock.side_effect = mock_get_setting

        # 3. Run scanner logic
        results = list(scan_library(db))
        
        # Assertions
        print("\nScan Results:")
        for r in results:
            print(f"  {r.get('status')}: {r.get('message')}")

        calls = db.add.call_args_list
        created_docs = []
        created_tasks = []
        for call in calls:
            obj = call[0][0]
            if isinstance(obj, models.Document):
                created_docs.append(obj.name)
            if isinstance(obj, models.Task):
                created_tasks.append(obj.name)
        
        print(f"\nCreated Documents (Orders): {created_docs}")
        print(f"Created Tasks: {created_tasks}")
        
        # Check root file transformation
        if "root_order" not in created_docs:
            print(f"FAIL: 'root_order' document missing. Found: {created_docs}")
            assert "root_order" in created_docs
        
        # Check deduplication
        if "dedupe.gnc" not in created_tasks:
            print(f"FAIL: 'dedupe.gnc' task missing. Found: {created_tasks}")
            assert "dedupe.gnc" in created_tasks
            
        if "dedupe_801.gnc" in created_tasks:
            print(f"FAIL: 'dedupe_801.gnc' task should be deduplicated. Found: {created_tasks}")
            assert "dedupe_801.gnc" not in created_tasks

        if "dedupe_to801.gnc" in created_tasks:
            print(f"FAIL: 'dedupe_to801.gnc' task should be deduplicated. Found: {created_tasks}")
            assert "dedupe_to801.gnc" not in created_tasks
        
        print("\nVerification SUCCESSFUL!")

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_scanner_logic()
