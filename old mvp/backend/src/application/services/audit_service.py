from typing import List
from src.infrastructure.database.audit_repository import SQLAuditRepository

class AuditService:
    def __init__(self, repo: SQLAuditRepository):
        self.repo = repo

    def list_logs(self, skip: int = 0, limit: int = 100) -> List[dict]:
        # Return as dicts for now as the repository uses AuditLogDB
        logs = self.repo.db.query(self.repo.db.get_model("AuditLogDB")).offset(skip).limit(limit).all()
        return [log.to_dict() if hasattr(log, "to_dict") else {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "actor": log.actor,
            "action_type": log.action_type,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "previous_value": log.previous_value,
            "new_value": log.new_value
        } for log in logs]
