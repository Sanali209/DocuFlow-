from sqlalchemy.orm import Session
from .models import AuditLogDB

class SQLAuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, actor: str, action_type: str, entity_type: str, entity_id: int = None, prev: str = None, new: str = None):
        log = AuditLogDB(
            actor=actor,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            previous_value=prev,
            new_value=new
        )
        self.db.add(log)
        self.db.commit()
