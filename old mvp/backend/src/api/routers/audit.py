from fastapi import APIRouter, Depends
from typing import List
from src.application.services.audit_service import AuditService
# We'll need a dependency for audit service
from src.api.dependencies import get_db, SessionLocal
from src.infrastructure.database.audit_repository import SQLAuditRepository

router = APIRouter(tags=["audit"])

def get_audit_service(db = Depends(get_db)):
    repo = SQLAuditRepository(db)
    return AuditService(repo)

@router.get("/audit-logs")
def read_audit_logs(skip: int = 0, limit: int = 100, service: AuditService = Depends(get_audit_service)):
    return service.list_logs(skip, limit)
