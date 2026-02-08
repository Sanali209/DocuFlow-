from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from .routers import documents, journal, inventory, production, gnc, settings, audit

# ... (omitted setup_sync and lifespan for brevity if use replace_file_content)
# Actually I should include the setup sync and lifespan if they are in between.
# Let's see the TargetContent.
from .middleware import AuditMiddleware
from .dependencies import SessionLocal
from .database import engine
from src.infrastructure.database.models import Base
from src.application.services.sync.manager import SyncManager
from src.application.services.sync.scanner import DirectoryScanner
from src.application.services.sync.processor import SyncProcessor
from src.application.services.settings_service import SettingsService

# Dependency Setup for Background Sync
def setup_sync():
    settings_service = SettingsService(SessionLocal)
    processor = SyncProcessor(SessionLocal)
    scanner = DirectoryScanner(processor)
    return SyncManager(scanner, settings_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB tables exist
    Base.metadata.create_all(bind=engine)
    
    # Startup: Start SyncService
    sync_manager = setup_sync()
    sync_manager.start()
    app.state.sync_manager = sync_manager
    yield
    # Shutdown: Stop SyncService
    sync_manager.stop()

app = FastAPI(title="DocuFlow Pro API", lifespan=lifespan)

app.add_middleware(AuditMiddleware)

# CORS cleanup as per plan
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: Move to config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents")
app.include_router(journal.router, prefix="/api/journal")
app.include_router(inventory.router, prefix="/api")
app.include_router(production.router, prefix="/api/jobs")
app.include_router(gnc.router, prefix="/api/gnc")
app.include_router(settings.router, prefix="/api")
app.include_router(audit.router, prefix="/api/audit")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    # If not an API request, serve index.html
    if not full_path.startswith("api/"):
        import os
        index_path = os.path.join("static", "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return {"detail": "Not Found"}
