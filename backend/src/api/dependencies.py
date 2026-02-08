from fastapi import Depends
from sqlalchemy.orm import Session
from src.infrastructure.database.material_repository import SQLMaterialRepository, SQLPartRepository, SQLStockRepository
from src.application.services.inventory_service import InventoryService
from src.infrastructure.database.repositories import SQLDocumentRepository, SQLTaskRepository
from src.application.services.document_service import DocumentService
from src.infrastructure.database.journal_repository import SQLJournalRepository
from src.application.services.journal_service import JournalService
from src.application.services.production_service import ProductionService
from src.application.services.gnc_service import GncService
from src.application.services.settings_service import SettingsService
from .database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_settings_service() -> SettingsService:
    return SettingsService(SessionLocal)

def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    repo = SQLDocumentRepository(db)
    return DocumentService(repo)

def get_journal_service(db: Session = Depends(get_db)) -> JournalService:
    repo = SQLJournalRepository(db)
    return JournalService(repo)

def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
    mat_repo = SQLMaterialRepository(db)
    part_repo = SQLPartRepository(db)
    stock_repo = SQLStockRepository(db)
    return InventoryService(mat_repo, part_repo, stock_repo)

def get_production_service(db: Session = Depends(get_db)) -> ProductionService:
    task_repo = SQLTaskRepository(db)
    doc_repo = SQLDocumentRepository(db)
    return ProductionService(task_repo, doc_repo)

def get_gnc_service() -> GncService:
    return GncService()
