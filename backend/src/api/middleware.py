from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from .dependencies import SessionLocal
from src.infrastructure.database.audit_repository import SQLAuditRepository

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Simple auditing for mutations
        if request.method in ["POST", "PUT", "DELETE", "PATCH"] and response.status_code < 400:
            actor = request.headers.get("X-User-Role", "unknown")
            # In a real app, we'd extract entity info from the request path or body
            # For now, minimal professional logging
            db = SessionLocal()
            try:
                repo = SQLAuditRepository(db)
                repo.create_log(
                    actor=actor,
                    action_type=request.method,
                    entity_type=request.url.path,
                    entity_id=None # Placeholder
                )
            except Exception as e:
                print(f"Audit Error: {e}")
            finally:
                db.close()
                
        return response
