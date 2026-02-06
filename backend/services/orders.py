from sqlalchemy.orm import Session
from .. import models, schemas
import os
import shutil
from typing import Any, List, Dict
from datetime import date

class OrderService:
    @staticmethod
    def create_order(db: Session, order_data: schemas.OrderCreate):
        # 1. Create Document
        doc = models.Document(
            name=order_data.name,
            type=models.DocumentType.ORDER,
            status=models.DocumentStatus.IN_PROGRESS,
            content=f"Order created with {len(order_data.parts)} unique parts.",
            # author set by router if available
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 2. Folder Generation
        from ..config import load_config
        config = load_config()
        mihtav_path = config.get("sync_mihtav_path", "storage/orders")
        
        # Sanitize name for folder
        safe_name = "".join(c for c in doc.name if c.isalnum() or c in (' ', '-', '_')).strip()
        order_dir = os.path.join(mihtav_path, safe_name)
        
        if not os.path.exists(order_dir):
            try:
                os.makedirs(order_dir, exist_ok=True)
                # Update doc content to reflect path if needed, or just log
            except Exception as e:
                print(f"Failed to create order directory: {e}")
        
        # 3. Create Tasks
        count = 0
        for item in order_data.parts:
            # item is { id: int, qty: int }
            part = db.query(models.Part).filter(models.Part.id == item.id).first()
            if not part:
                continue
            
            for _ in range(item.qty):
                count += 1
                task = models.Task(
                    document_id=doc.id,
                    name=f"{part.name} - #{count}",
                    status=models.TaskStatus.PLANNED,
                    material_id=part.material_id,
                )
                db.add(task)
                db.flush() # Get ID
                
                # Link Task to Part
                task_part = models.TaskPart(
                    task_id=task.id,
                    part_id=part.id,
                    quantity=1 # One task per physical part instance
                )
                db.add(task_part)
        
        db.commit()
        return doc

    @staticmethod
    def save_multi_sheet_order(db: Session, sheets_data: List[Dict[str, Any]], name: str, original_doc_id: int = None):
        """
        Creates a new Order from a multi-sheet nesting result.
        Persistence: Document -> Folder -> [GNC Files, nesting_project.json]
        Also creates and links Tasks.
        """
        from ..gnc_parser import GNCSheet
        from ..gnc_generator import GNCGenerator
        from ..config import load_config
        import json
        from datetime import date
        
        # 1. Create Document
        doc = models.Document(
            name=name,
            type=models.DocumentType.ORDER,
            status=models.DocumentStatus.IN_PROGRESS,
            content=f"Created from nesting of Document #{original_doc_id}" if original_doc_id else "Created GNC nesting project",
            registration_date=date.today()
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 2. Setup Folder
        base_path = "static/uploads/gncEditor"
        safe_name = "".join(c for c in doc.name if c.isalnum() or c in (' ', '-', '_')).strip()
        order_folder = f"{doc.id}_{safe_name}"
        order_dir = os.path.join(base_path, order_folder)
        os.makedirs(order_dir, exist_ok=True)

        generator = GNCGenerator()
        
        # 4. Process Sheets & Create Tasks
        updated_sheets = []
        for i, sheet_dict in enumerate(sheets_data):
            s_data = sheet_dict.get('data', {})
            s_name = sheet_dict.get('name', f"Sheet_{i+1}")
            
            gnc_sheet = GNCSheet(**s_data)
            
            safe_sheet_name = "".join(c for c in s_name if c.isalnum() or c in (' ', '-', '_')).strip()
            gnc_filename = f"{safe_sheet_name}.gnc"
            gnc_path = os.path.join(order_dir, gnc_filename)
            
            content = generator.generate(gnc_sheet)
            with open(gnc_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            task = models.Task(
                document_id=doc.id,
                name=s_name,
                status=models.TaskStatus.PLANNED,
                gnc_file_path=gnc_path
            )
            
            if gnc_sheet.material:
                material = db.query(models.Material).filter(models.Material.name == gnc_sheet.material).first()
                if material:
                    task.material_id = material.id
            
            db.add(task)
            db.flush() # Get task.id
            
            # Update sheet data with task_id for persistence
            s_data['task_id'] = task.id
            s_data['name'] = s_name
            updated_sheets.append({
                "id": i,
                "name": s_name,
                "data": s_data
            })
            
            # Link Parts to this Task
            for part in gnc_sheet.parts:
                source_part_id = part.metadata.get('source_part_id')
                if source_part_id:
                    task_part = models.TaskPart(
                        task_id=task.id,
                        part_id=source_part_id,
                        quantity=1
                    )
                    db.add(task_part)

        # 5. Save Project State for Editing (with task IDs)
        project_state_path = os.path.join(order_dir, "nesting_project.json")
        with open(project_state_path, 'w', encoding='utf-8') as f:
            json.dump({
                "name": name,
                "order_id": doc.id,
                "original_document_id": original_doc_id,
                "sheets": updated_sheets
            }, f, indent=2)

        db.commit()
        return doc

    @staticmethod
    def update_order_nesting(db: Session, order_id: int, sheets_data: List[Dict[str, Any]]):
        """
        Updates an existing Order with new nesting data.
        Regenerates GNC files and updates nesting_project.json.
        Syncs Tasks and TaskPart associations.
        """
        from ..gnc_parser import GNCSheet
        from ..gnc_generator import GNCGenerator
        import json

        doc = db.query(models.Document).filter(models.Document.id == order_id).first()
        if not doc:
            raise Exception("Order not found")

        # Calculate folder
        base_path = "static/uploads/gncEditor"
        safe_name = "".join(c for c in doc.name if c.isalnum() or c in (' ', '-', '_')).strip()
        order_folder = f"{doc.id}_{safe_name}"
        order_dir = os.path.join(base_path, order_folder)
        os.makedirs(order_dir, exist_ok=True)

        generator = GNCGenerator()
        
        updated_sheets = []
        active_task_ids = []

        # Regenerate GNC files and sync tasks
        for i, sheet_dict in enumerate(sheets_data):
            s_data = sheet_dict.get('data', {})
            s_name = sheet_dict.get('name', f"Sheet_{i+1}")
            t_id = s_data.get('task_id')
            
            gnc_sheet = GNCSheet(**s_data)
            
            safe_sheet_name = "".join(c for c in s_name if c.isalnum() or c in (' ', '-', '_')).strip()
            gnc_path = os.path.join(order_dir, f"{safe_sheet_name}.gnc")
            
            content = generator.generate(gnc_sheet)
            with open(gnc_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Find or Create Task
            task = None
            if t_id:
                task = db.query(models.Task).filter(models.Task.id == t_id, models.Task.document_id == doc.id).first()
            
            if not task:
                # Try by name as fallback
                task = db.query(models.Task).filter(models.Task.document_id == doc.id, models.Task.name == s_name).first()

            if task:
                task.name = s_name
                task.gnc_file_path = gnc_path
            else:
                task = models.Task(
                    document_id=doc.id,
                    name=s_name,
                    status=models.TaskStatus.PLANNED,
                    gnc_file_path=gnc_path
                )
                db.add(task)
            
            if gnc_sheet.material:
                material = db.query(models.Material).filter(models.Material.name == gnc_sheet.material).first()
                if material:
                    task.material_id = material.id
            
            db.flush()
            active_task_ids.append(task.id)
            s_data['task_id'] = task.id
            s_data['name'] = s_name
            updated_sheets.append({
                "id": i,
                "name": s_name,
                "data": s_data
            })

            # Sync TaskPart associations
            db.query(models.TaskPart).filter(models.TaskPart.task_id == task.id).delete()
            for part in gnc_sheet.parts:
                source_part_id = part.metadata.get('source_part_id')
                if source_part_id:
                    task_part = models.TaskPart(
                        task_id=task.id,
                        part_id=source_part_id,
                        quantity=1
                    )
                    db.add(task_part)

        # Cleanup Orphaned Tasks (tasks that were sheets but aren't anymore)
        # Note: We only delete if they have a GNC file path in our editor dir
        orphans = db.query(models.Task).filter(
            models.Task.document_id == doc.id,
            ~models.Task.id.in_(active_task_ids),
            models.Task.gnc_file_path.like(f"%{order_folder}%")
        ).all()
        for o in orphans:
            db.delete(o)

        # Update Project State
        project_state_path = os.path.join(order_dir, "nesting_project.json")
        with open(project_state_path, 'w', encoding='utf-8') as f:
            json.dump({
                "name": doc.name,
                "order_id": doc.id,
                "sheets": updated_sheets
            }, f, indent=2)
        
        db.commit()
        return doc
