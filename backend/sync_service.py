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

    def _scan_mihtav(self, db: Session, root_path: str):
        if not os.path.exists(root_path):
            return

        # Walk through the directory
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.lower().endswith('.gnc'):
                    file_path = os.path.join(root, file)
                    self._process_mihtav_file(db, file_path)

    def _process_mihtav_file(self, db: Session, file_path: str):
        # Logic to process order file

        filename = os.path.basename(file_path)

        # Check if attachment exists with this exact path
        existing_att = db.query(models.Attachment).filter(models.Attachment.file_path == file_path).first()
        if existing_att:
            return # Already imported

        # Parse GNC
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # parser = GNCParser()
            # sheet = parser.parse(content, filename=filename)
            # Parsing might be heavy, maybe just link it first?
            # But we need metadata.

            # Let's assume parent folder name is the Order Name.
            order_name = os.path.basename(os.path.dirname(file_path))

            # Find or Create Document
            doc = db.query(models.Document).filter(models.Document.name == order_name, models.Document.type == models.DocumentType.PLAN).first()
            if not doc:
                doc = models.Document(
                    name=order_name,
                    type=models.DocumentType.PLAN,
                    status=models.DocumentStatus.IN_PROGRESS,
                    registration_date=date.today(),
                    description="Auto-imported from Mihtav"
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)

            # Add Attachment
            att = models.Attachment(
                document_id=doc.id,
                file_path=file_path, # Store absolute path for network files
                filename=filename,
                media_type="application/x-gnc",
                created_at=date.today()
            )
            db.add(att)
            db.commit()

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")

    def _scan_sidra(self, db: Session, root_path: str):
        if not os.path.exists(root_path):
            return

        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.lower().endswith('.gnc'):
                    file_path = os.path.join(root, file)
                    self._process_sidra_file(db, file_path)

    def _process_sidra_file(self, db: Session, file_path: str):
        filename = os.path.basename(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            parser = GNCParser()
            sheet = parser.parse(content, filename=filename)

            reg_num = filename.replace(".gnc", "").replace(".GNC", "")
            version = "A"

            # Attempt to extract from filename if format is "REG_VER"
            if "_" in reg_num:
                parts = reg_num.split("_")
                reg_num = parts[0]
                version = parts[-1]

            # Check DB
            part = db.query(models.Part).filter(models.Part.registration_number == reg_num, models.Part.version == version).first()

            if not part:
                # Create
                mat_name = sheet.material or "Unknown"
                material = None
                if mat_name:
                    material = db.query(models.Material).filter(models.Material.name == mat_name).first()
                    if not material:
                        material = models.Material(name=mat_name)
                        db.add(material)
                        db.commit()
                        db.refresh(material)

                part = models.Part(
                    name=filename,
                    registration_number=reg_num,
                    version=version,
                    material_id=material.id if material else None,
                    gnc_file_path=file_path,
                    width=sheet.width or 0.0,
                    height=sheet.height or 0.0
                )
                db.add(part)
                db.commit()
            else:
                if part.gnc_file_path != file_path:
                    part.gnc_file_path = file_path
                    db.commit()

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
