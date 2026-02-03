import os
import shutil
import tempfile
import sys
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scanner import scan_library
from backend import models
from backend.sync_service import SyncService

def test_refactor_scanner():
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Setup mihtav path (MAIL)
        mihtav_path = os.path.normpath(os.path.abspath(os.path.join(temp_dir, "mihtav")))
        os.makedirs(mihtav_path)
        
        # Case A: File in root -> Document (MAIL)
        root_file = os.path.join(mihtav_path, "RootFileDoc.gnc")
        with open(root_file, 'w') as f: f.write("(PART NAME: ROOT)\n")
        
        # Case B: Directory in root -> Document (MAIL), Files -> Tasks
        order_dir = os.path.join(mihtav_path, "OrderDir")
        os.makedirs(order_dir)
        task1 = os.path.join(order_dir, "Task1.gnc")
        with open(task1, 'w') as f: f.write("(PART NAME: T1)\n")
        
        # Case C: Deduplication in Directory
        task2 = os.path.join(order_dir, "Task2.gnc")
        task2_801 = os.path.join(order_dir, "Task2_801.gnc")
        with open(task2, 'w') as f: f.write("(PART NAME: T2)\n")
        with open(task2_801, 'w') as f: f.write("(PART NAME: T2_801)\n")

        # 2. Setup sidra path (PLAN)
        sidra_path = os.path.normpath(os.path.abspath(os.path.join(temp_dir, "sidra")))
        os.makedirs(sidra_path)
        
        # Case D: File in root -> Document (PLAN)
        plan_file = os.path.join(sidra_path, "PlanFile.gnc")
        with open(plan_file, 'w') as f: f.write("(PART NAME: P1)\n")

        # 3. Mock DB
        db = MagicMock()
        
        # Mock queries to always return None (create new)
        def mock_query(model):
            query = MagicMock()
            query.filter.return_value = query
            query.first.return_value = None 
            return query
        db.query.side_effect = mock_query

        # 4. Run Scanner
        print("Running Scanner...")
        # scan_library(db) reads from settings. We mock crud.get_setting.
        
        # We need to mock crud.get_setting inside scanner
        with patch('backend.crud.get_setting') as mock_get_setting:
            def side_effect(db, key):
                if key == 'sync_mihtav_path': return MagicMock(value=mihtav_path)
                if key == 'sync_sidra_path': return MagicMock(value=sidra_path)
                return None
            mock_get_setting.side_effect = side_effect
            
            # Re-import scanner to apply patches if needed? No, patch applies to where it is used.
            # But scan_library imports crud. 
            pass 

            # Actually, scan_library in `scanner.py` uses `crud.get_setting`.
            # Let's just run it, assuming we patch it correctly.
            
            # Wait, `scan_library` implementation I wrote earlier takes paths from `crud`?
            # Let's check `scanner.py` content again.
            # I replaced the content. I need to be sure.
            
            # START_TEMPORARY_CHECK
            # I will check scanner.py content via view_file if I am unsure, but I just wrote it.
            # It reads paths from args usually? 
            # Original: `def scan_library(db: Session):`
            # Inside: `mihtav_path = crud.get_setting(...)`
            # So patching backend.crud.get_setting is correct.
            
            # Call scan_library with just db, relied on mocked settings
            list(scan_library(db))

        # 5. Verify DB Calls
        # We need to capture what Documents and Tasks were added.
        
        added_docs = []
        added_tasks = []
        
        for call in db.add.call_args_list:
            obj = call[0][0]
            if isinstance(obj, models.Document):
                added_docs.append(obj)
            if isinstance(obj, models.Task):
                added_tasks.append(obj)
                
        print(f"Added Docs: {[d.name + ':' + str(d.type) for d in added_docs]}")
        print(f"Added Tasks: {[t.name for t in added_tasks]}")
        
        # Assertions
        
        # MIHTAV (MAIL)
        # RootFileDoc
        doc_root = next((d for d in added_docs if d.name == "RootFileDoc"), None)
        assert doc_root, "RootFileDoc not found"
        assert doc_root.type == models.DocumentType.MAIL, f"RootFileDoc type mismatch: {doc_root.type}"
        
        # OrderDir
        doc_order = next((d for d in added_docs if d.name == "OrderDir"), None)
        assert doc_order, "OrderDir not found"
        assert doc_order.type == models.DocumentType.MAIL, f"OrderDir type mismatch: {doc_order.type}"
        
        # SIDRA (PLAN)
        # PlanFile
        doc_plan = next((d for d in added_docs if d.name == "PlanFile"), None)
        assert doc_plan, "PlanFile not found"
        assert doc_plan.type == models.DocumentType.PLAN, f"PlanFile type mismatch: {doc_plan.type}"
        
        # TASKS
        # RootFileDoc Task
        task_root = next((t for t in added_tasks if t.name == "RootFileDoc.gnc"), None)
        assert task_root, "RootFileDoc.gnc task not found"
        
        # OrderDir Tasks
        task1 = next((t for t in added_tasks if t.name == "Task1.gnc"), None)
        assert task1, "Task1.gnc not found"
        
        task2 = next((t for t in added_tasks if t.name == "Task2.gnc"), None)
        assert task2, "Task2.gnc not found"
        
        # Deduplication
        task2_801 = next((t for t in added_tasks if t.name == "Task2_801.gnc"), None)
        assert not task2_801, "Task2_801.gnc should be deduplicated"
        
        print("Verification SUCCESSFUL")

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_refactor_scanner()
