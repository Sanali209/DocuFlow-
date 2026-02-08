import os
import logging
from datetime import date
from sqlalchemy.orm import Session
from src.domain.interfaces import IDocumentRepository
from src.domain.models import Document, DocumentType, DocumentStatus
# More imports needed for GNC parsing and models

logger = logging.getLogger(__name__)

from src.infrastructure.parsers.gnc_parser import GNCParser
from src.infrastructure.graphics.svg_generator import SVGGenerator
from src.infrastructure.database.models import DocumentDB, AttachmentDB, MaterialDB, PartDB, TaskDB

class SyncProcessor:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.parser = GNCParser()
        self.svg_gen = SVGGenerator()
        
        # Path for thumbnails
        # Path for thumbnails
        # From backend/src/application/services/sync/processor.py to root/static
        # __file__ is processor.py
        # 1. sync/
        # 2. services/
        # 3. application/
        # 4. src/
        # 5. backend/
        # 6. root/
        levels_up = 6
        path = os.path.abspath(__file__)
        for _ in range(levels_up):
            path = os.path.dirname(path)
        base_dir = path
        self.thumbnail_dir = os.path.join(base_dir, "static", "uploads", "thumbnails")
        os.makedirs(self.thumbnail_dir, exist_ok=True)

    def process_file(self, file_path: str, source_type: str, doc_name: str = None):
        db = self.db_session_factory()
        try:
            filename = os.path.basename(file_path)
            
            # 1. Check if Attachment exists
            existing_att = db.query(AttachmentDB).filter(AttachmentDB.file_path == file_path).first()
            if existing_att: return

            # 2. Determine Document Type & Status
            doc_type = "order" if source_type == "mihtav" else "part"
            if not doc_name:
                doc_name = filename.replace(".gnc", "").replace(".GNC", "")
            
            # 3. Parse GNC
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                sheet = self.parser.parse(content, filename=filename)
            except Exception as e:
                logger.error(f"Failed to parse {filename}: {e}")
                sheet = None

            # 4. Get/Create Document
            doc = db.query(DocumentDB).filter(DocumentDB.name == doc_name, DocumentDB.type == doc_type).first()
            if not doc:
                doc = DocumentDB(
                    name=doc_name,
                    type=doc_type,
                    status="unregistered",
                    registration_date=date.today(),
                    description=f"Auto-imported from {source_type}"
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)

            # 5. Create Attachment
            att = AttachmentDB(
                document_id=doc.id,
                file_path=file_path,
                filename=filename,
                media_type="application/x-gnc"
            )
            db.add(att)
            db.commit()

            # 6. Extract & Update Part/Task library
            if sheet:
                self._update_part_library(db, sheet, filename, file_path)
                self._process_tasks(db, doc, sheet, file_path, filename)
            
        except Exception as e:
            logger.error(f"Sync error for {file_path}: {e}")
            db.rollback()
        finally:
            db.close()

    def _update_part_library(self, db: Session, sheet, filename: str, file_path: str):
        # Professional implementation of registration number and version logic
        reg_num = filename.replace(".gnc", "").replace(".GNC", "")
        version = "A"
        if "_" in reg_num and "801" not in reg_num:
            parts = reg_num.split("_")
            reg_num = parts[0]
            version = parts[-1]

        part = db.query(PartDB).filter(PartDB.registration_number == reg_num).first()
        
        # Material Handling
        mat_name = getattr(sheet, 'material', 'Unknown') or "Unknown"
        material = db.query(MaterialDB).filter(MaterialDB.name == mat_name).first()
        if not material and mat_name != "Unknown":
            material = MaterialDB(name=mat_name)
            db.add(material)
            db.commit()
            db.refresh(material)

        # Dimension extraction
        width = getattr(sheet, 'width', 0.0)
        height = getattr(sheet, 'height', 0.0)

        if not part:
            part = PartDB(
                name=filename,
                registration_number=reg_num,
                version=version,
                material_id=material.id if material else None,
                gnc_file_path=file_path,
                width=width,
                height=height
            )
            db.add(part)
        else:
            # Update existing part metadata
            part.gnc_file_path = file_path
            if part.width == 0:
                part.width = width
                part.height = height
        db.commit()

    def _process_tasks(self, db: Session, doc: DocumentDB, sheet, file_path: str, filename: str):
        # Link to tasks
        task = db.query(TaskDB).filter(TaskDB.document_id == doc.id, TaskDB.gnc_file_path == file_path).first()
        if not task:
            task = TaskDB(
                document_id=doc.id,
                name=filename,
                gnc_file_path=file_path,
                status="planned"
            )
            db.add(task)
            db.commit()
