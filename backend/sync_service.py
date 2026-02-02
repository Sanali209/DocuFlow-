import time
import os
import threading
import logging
from sqlalchemy.orm import Session
from datetime import date
from .database import SessionLocal
from . import crud, models, schemas
from .gnc_parser import GNCParser

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self):
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()

    def start(self):
        if self.running:
            return
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("SyncService started")

    def stop(self):
        if not self.running:
            return
        self.running = False
        self._stop_event.set()
        if self.thread:
            self.thread.join()
        logger.info("SyncService stopped")

    def _run_loop(self):
        logger.info("SyncService loop running...")
        while self.running:
            try:
                self._sync_cycle()
            except Exception as e:
                logger.error(f"Error in sync cycle: {e}")

            # Wait for next cycle or stop event
            if self._stop_event.wait(timeout=30): # 30 seconds interval
                break

    def _sync_cycle(self):
        db = SessionLocal()
        try:
            # Get Config
            mihtav_path_setting = crud.get_setting(db, "sync_mihtav_path")
            sidra_path_setting = crud.get_setting(db, "sync_sidra_path")

            if mihtav_path_setting and mihtav_path_setting.value:
                self._scan_mihtav(db, mihtav_path_setting.value)

            if sidra_path_setting and sidra_path_setting.value:
                self._scan_sidra(db, sidra_path_setting.value)

        finally:
            db.close()

    def _process_gnc_file(self, db: Session, file_path: str, source_type: str):
        try:
            filename = os.path.basename(file_path)
            
            # 1. Check if Attachment exists (Avoid duplicates)
            existing_att = db.query(models.Attachment).filter(models.Attachment.file_path == file_path).first()
            if existing_att:
                return

            # 2. Determine Document Type & Name
            # For Mihtav (Orders), folder name is usually the Order Name.
            # For Sidra (Parts), filename is the Part Name.
            
            if source_type == "mihtav":
                doc_name = os.path.basename(os.path.dirname(file_path))
                doc_type = models.DocumentType.ORDER
            else:
                doc_name = filename.replace(".gnc", "").replace(".GNC", "")
                doc_type = models.DocumentType.PART # Assuming PART type exists or use PLAN
                if not hasattr(models.DocumentType, 'PART'):
                     doc_type = models.DocumentType.PLAN

            # 3. Parse GNC for Metadata
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            parser = GNCParser()
            try:
                sheet = parser.parse(content, filename=filename)
            except Exception as e:
                logger.error(f"Failed to parse {filename}: {e}")
                sheet = None

            # Detect 801 (Machine Edit)
            is_801 = "_801" in filename or (sheet and not parser.office_mode)
            description = f"Auto-imported from {source_type.title()}"
            if is_801:
                description += ". Machine Edit Detected (_801)."

            # 4. Find or Create Document
            # Only create NEW document if it doesn't exist. 
            # For Orders, we might add multiple files to ONE document (Order).
            # For Parts, it's 1-to-1 usually.
            
            doc = db.query(models.Document).filter(models.Document.name == doc_name, models.Document.type == doc_type).first()
            
            if not doc:
                # FR-08 / PRD 3.4: Create as UNREGISTERED
                status = models.DocumentStatus.UNREGISTERED if hasattr(models.DocumentStatus, 'UNREGISTERED') else models.DocumentStatus.IN_PROGRESS
                
                doc = models.Document(
                    name=doc_name,
                    type=doc_type,
                    status=status,
                    registration_date=date.today(),
                    description=description,
                    content=f"Imported from {file_path}"
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
            else:
                # Update description if 801 found and not noted?
                if is_801 and "Machine Edit" not in (doc.description or ""):
                    doc.description = (doc.description or "") + ". Machine Edit Detected (_801)."
                    db.commit()

            # 5. Create Attachment linkage
            att = models.Attachment(
                document_id=doc.id,
                file_path=file_path,
                filename=filename,
                media_type="application/x-gnc",
                created_at=date.today()
            )
            db.add(att)
            db.commit()

            # 6. Extract & Update Part (Sidra Library Population)
            # Even metadata from Orders (Mihtav) can populate Parts Library if new.
            if sheet:
                self._update_part_library(db, sheet, filename, file_path)

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")

    def _update_part_library(self, db: Session, sheet, filename: str, file_path: str):
        try:
            # Registration Number Logic
            reg_num = filename.replace(".gnc", "").replace(".GNC", "")
            version = "A"
            if "_" in reg_num and "801" not in reg_num: # Simple version check
                parts = reg_num.split("_")
                reg_num = parts[0]
                version = parts[-1]
            
            # Check if Part exists
            part = db.query(models.Part).filter(models.Part.registration_number == reg_num).first()
            # Note: We might want to filter by Version too, but often we just want the latest linkage.
            
            # Material Handling
            mat_name = sheet.material or "Unknown"
            material = None
            if mat_name != "Unknown":
                material = db.query(models.Material).filter(models.Material.name == mat_name).first()
                if not material:
                    try:
                        material = models.Material(name=mat_name)
                        db.add(material)
                        db.commit()
                        db.refresh(material)
                    except Exception:
                        db.rollback()
                        material = db.query(models.Material).filter(models.Material.name == mat_name).first()

            # Calculate Dimensions
            width = sheet.program_width or sheet.width or 0.0
            height = sheet.program_height or sheet.height or 0.0
            
            # Stats Collection for Research/Reverse Eng.
            stats = {
                "total_contours": sheet.total_contours,
                "total_parts": sheet.total_parts,
            }

            # Extract P-Codes from contours for "Harmonization"
            p_codes = {}
            for p in sheet.parts:
                for c in p.contours:
                    for k, v in c.metadata.items():
                        if k.startswith("P"):
                            if k not in p_codes:
                                p_codes[k] = []
                            if v not in p_codes[k]:
                                p_codes[k].append(v)

            stats["p_codes"] = p_codes

            # Approximate holes
            if sheet.total_contours > 1:
                stats["approx_holes"] = sheet.total_contours - 1

            stats_json = json.dumps(stats)
            
            if not part:
                part = models.Part(
                    name=filename,
                    registration_number=reg_num,
                    version=version,
                    material_id=material.id if material else None,
                    gnc_file_path=file_path,
                    width=width,
                    height=height,
                    stats=stats_json
                )
                db.add(part)
                db.commit()
            else:
                # Update existing part with better data?
                # If this file is newer or better source?
                # For now, just ensure file path is linked if missing
                if not part.gnc_file_path:
                    part.gnc_file_path = file_path

                # Update dimensions if zero
                if part.width == 0 and width > 0:
                    part.width = width
                    part.height = height
                    part.material_id = material.id if material else part.material_id

                # Update stats (always update to capture latest metadata)
                part.stats = stats_json

                db.commit()
                    
        except Exception as e:
            logger.error(f"Failed to update part library for {filename}: {e}")

    def _scan_mihtav(self, db: Session, root_path: str):
        if not os.path.exists(root_path): return
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.lower().endswith('.gnc'):
                    self._process_gnc_file(db, os.path.join(root, file), "mihtav")

    def _scan_sidra(self, db: Session, root_path: str):
        if not os.path.exists(root_path): return
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.lower().endswith('.gnc'):
                     self._process_gnc_file(db, os.path.join(root, file), "sidra")
