import os
import shutil
import logging
from typing import List, Optional
from datetime import datetime
from src.application.services.document_service import DocumentService
from src.domain.models import Document, Task
from src.application.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

class OrderScanner:
    def __init__(self, document_service: DocumentService, settings_service: SettingsService):
        self.document_service = document_service
        self.settings_service = settings_service

    def scan_and_process(self, root_path: str, source_type: str):
        """
        Scans specific root path (Sidra/Michtaw).
        Workflow:
        1. Check 'in' folder for directories (Orders).
        2. Create Order (Document).
        3. Scan contents for GNC/Tasks.
        4. Move folder to 'registered'.
        """
        self._process_root(root_path, source_type)

    def _process_root(self, root_path: str, source_type: str):
        in_path = os.path.join(root_path, "in")
        registered_path = os.path.join(root_path, "registred")

        if not os.path.exists(in_path):
            return

        os.makedirs(registered_path, exist_ok=True)

        try:
            with os.scandir(in_path) as it:
                for entry in it:
                    if entry.is_dir():
                        self._process_order_folder(entry, registered_path, source_type)
        except OSError as e:
            logger.error(f"Error scanning {in_path}: {e}")

    def _process_order_folder(self, entry: os.DirEntry, registered_path: str, source_type: str):
        order_name = entry.name
        logger.info(f"Found new order folder: {order_name} in {source_type}")

        # 1. Create Order Document
        # Check if exists? For now, assume new or update.
        # We might want to avoid duplicates if it was already processed but not moved? 
        # But if it is in 'in', we assume it needs processing.
        
        # Create Document (Order)
        try:
            doc = self.document_service.doc_repo.get_by_name(order_name)
            if not doc:
                 doc = self.document_service.create_order(order_name, []) # Create empty order
                 logger.info(f"Created new order document: {order_name}")
            else:
                 logger.info(f"Order {order_name} already exists, updating tasks.")

            # 2. Scan for GNC/Tasks
            tasks_found = []
            for root, dirs, files in os.walk(entry.path):
                for file in files:
                    if file.lower().endswith('.gnc') or file.lower().endswith('.nc'):
                        # This is a task/part
                        task_name = os.path.splitext(file)[0]
                        file_path = os.path.join(root, file)
                        
                        # Check logic: "files details to library with checking they dublications"
                        # For now, just add as Task to Order.
                        
                        # Add task to order if not exists
                        # We need a method in doc_repo or service to add task safely
                        tasks_found.append({
                            "name": task_name,
                            "gnc_file_path": file_path,
                            "status": "planned",
                            "quantity": 1 # Default, maybe parse from name?
                        })

            # Batch add tasks
            if tasks_found:
                self.document_service.doc_repo.add_tasks_to_document(doc.id, tasks_found)

            # 3. Move to 'registred'
            # Move the entire folder
            dest_path = os.path.join(registered_path, order_name)
            
            # Handle collision in registered
            if os.path.exists(dest_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = os.path.join(registered_path, f"{order_name}_{timestamp}")
            
            shutil.move(entry.path, dest_path)
            logger.info(f"Moved {order_name} to {dest_path}")
            
            # Update file paths in DB?
            # If we moved the files, the paths in DB (gnc_file_path) are now wrong!
            # We must update them.
            
            # Recalculate paths based on new location
            # Or better: Move FIRST, then scan and create tasks.
            
        except Exception as e:
            logger.error(f"Failed to process order {order_name}: {e}")

