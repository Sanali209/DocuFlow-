import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from . import crud, models, schemas
from .database import SessionLocal, engine
from .sync_service import SyncService
from .routers import documents, tasks, settings, assignees, orders, parts_gnc
from .startup import router as startup_router
from .gnc_endpoints import router as gnc_router
from .warehouse import router as warehouse_router

# Create tables
try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Startup Warning: Could not initialize database tables. Connection might be invalid. Error: {e}")

# Migration for new columns in documents
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN author TEXT"))
        conn.commit()
    except Exception:
        pass

    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN description TEXT"))
        conn.commit()
    except Exception:
        pass

    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN done_date DATE"))
        conn.commit()
    except Exception:
        pass

    # Ensure content column exists (legacy migration)
    try:
        conn.execute(text("ALTER TABLE documents ADD COLUMN content TEXT"))
        conn.commit()
    except Exception:
        pass

    # Add material_id column to tasks
    try:
        conn.execute(text("ALTER TABLE tasks ADD COLUMN material_id INTEGER REFERENCES materials(id)"))
        conn.commit()
    except Exception:
        pass

    # Add gnc_file_path column to tasks
    try:
        conn.execute(text("ALTER TABLE tasks ADD COLUMN gnc_file_path TEXT"))
        conn.commit()
    except Exception:
        pass

    # Migration for TaskPart quantity
    try:
        # Check if quantity column exists in task_parts
        # SQLite specific check
        result = conn.execute(text("PRAGMA table_info(task_parts)"))
        columns = [row[1] for row in result.fetchall()]
        if 'quantity' not in columns:
            conn.execute(text("ALTER TABLE task_parts ADD COLUMN quantity INTEGER DEFAULT 1"))
            conn.commit()
            print("Migrated task_parts: Added quantity column")
    except Exception as e:
        print(f"Migration Warning: Could not migrate task_parts: {e}")

# Ensure upload directory
os.makedirs("static/uploads", exist_ok=True)

sync_service = SyncService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    sync_service.start()
    yield
    # Shutdown
    sync_service.stop()

app = FastAPI(lifespan=lifespan)

# Include Routers
app.include_router(startup_router)
app.include_router(gnc_router)
app.include_router(warehouse_router)
app.include_router(documents.router)
app.include_router(tasks.router)
app.include_router(settings.router)
app.include_router(assignees.router)
app.include_router(orders.router)
app.include_router(parts_gnc.router)

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only log state-changing methods
        if request.method in ["POST", "PUT", "DELETE", "PATCH"] and response.status_code < 400:
            try:
                # We use a separate session for logging to not interfere with request scope
                db = SessionLocal()

                # Determine Entity Type and ID from URL
                path_parts = request.url.path.strip("/").split("/")
                entity_type = path_parts[0] if path_parts else "unknown"
                entity_id = None
                # Check if second part is ID
                if len(path_parts) > 1 and path_parts[1].isdigit():
                    entity_id = int(path_parts[1])

                # Capture Query Params as extra info if no ID
                extra_info = str(request.query_params) if request.query_params else ""

                log = schemas.AuditLogCreate(
                    actor="system", # TODO: Extract from auth header if available
                    action_type=request.method,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    new_value=f"Success. {extra_info}"
                )
                crud.create_audit_log(db, log)
                db.close()
            except Exception as e:
                print(f"Audit Log Error: {e}")

        return response

app.add_middleware(AuditMiddleware)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
origins = [origin.strip() for origin in allowed_origins.split(",")] if allowed_origins else []
origins.extend([
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "*" # For sandbox
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files (Svelte)
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    app.mount("/uploads", StaticFiles(directory="static/uploads"), name="uploads")
    
    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join("static", full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # Otherwise serve index.html
        return FileResponse("static/index.html")
