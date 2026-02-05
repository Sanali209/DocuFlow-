from sqlalchemy.orm import Session
from .. import models, schemas
import os
import shutil
from typing import Any
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
    def save_order_from_nested_sheet(db: Session, sheet_data: Any, name: str, original_doc_id: int = None):
        """
        Creates a new Order Document from a nested GNC Sheet.
        Generates the GNC file and creates Tasks for each part on the sheet.
        """
        from ..gnc_parser import GNCSheet
        from ..gnc_generator import GNCGenerator
        
        # 1. Parse/Validate Sheet Data (since it comes as dict/json)
        # Verify if sheet_data is already a GNCSheet object or dict
        if isinstance(sheet_data, dict):
             # Ensure parts have x/y for the generator to use (even if not in Pydantic logic strictly, needed for generator)
             pass
        
        # Re-construct GNCSheet object to ensure validation
        # We need to handle 'parts' recursively if they are just dicts
        # Pydantic should handle this if we use GNCSheet(**sheet_data)
        # But GNCSheet parts might have extra fields (x, y) that are not in GNCPart model?
        # If GNCPart model doesn't have x/y, Pydantic will strip them?
        # YES.
        # PROBLEM: I updated GNCGenerator to use x/y. But I haven't updated GNCPart model.
        # If I validated with GNCSheet, x/y are GONE.
        # I MUST update GNCPart model in `gnc_parser.py` to include x/y (Optional).

        # Assuming GNCPart model is updated (I will do this next/concurrently)
        gnc_sheet = GNCSheet(**sheet_data)

        # 2. Create Document
        doc = models.Document(
            name=name,
            type=models.DocumentType.ORDER,
            status=models.DocumentStatus.IN_PROGRESS,
            content=f"Created from nesting of Document #{original_doc_id}" if original_doc_id else "Created from nesting",
            registration_date=date.today()
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 3. Create Folder & Save GNC
        from ..config import load_config
        config = load_config()
        mihtav_path = config.get("sync_mihtav_path", "storage/orders")
        
        safe_name = "".join(c for c in doc.name if c.isalnum() or c in (' ', '-', '_')).strip()
        order_dir = os.path.join(mihtav_path, safe_name)
        os.makedirs(order_dir, exist_ok=True)

        gnc_filename = f"{safe_name}.gnc"
        gnc_path = os.path.join(order_dir, gnc_filename)

        # Generate Content
        generator = GNCGenerator()
        # We must pass the raw sheet_data or ensure gnc_sheet has x/y
        # If I update GNCPart model, gnc_sheet will have x/y.
        content = generator.generate(gnc_sheet)
        
        with open(gnc_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Update Doc with path? Currently tasks link to GNC path? No, parts do.
        # Or Document tracks it locally?
        # Usually we might add a main task or just rely on folder structure.

        # 4. Create Tasks
        count = 0
        for part in gnc_sheet.parts:
            count += 1
            # Retrieve source info
            source_part_id = part.metadata.get('source_part_id')
            
            task_name = part.name or f"Part #{count}"
            
            task = models.Task(
                document_id=doc.id,
                name=task_name,
                status=models.TaskStatus.PLANNED,
                # material? Use sheet material
            )
            
            # Find material?
            if source_part_id:
                source_part = db.query(models.Part).filter(models.Part.id == source_part_id).first()
                if source_part:
                     task.material_id = source_part.material_id

            db.add(task)
            db.flush()

            if source_part_id:
                task_part = models.TaskPart(
                    task_id=task.id,
                    part_id=source_part_id,
                    quantity=1
                )
                db.add(task_part)

        db.commit()
        return doc
