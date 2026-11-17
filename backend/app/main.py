"""
FastAPI Main Application Entrypoint for Industrial Conveyor Belt BOM Vision Inspector.
"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings, STATIC_AUDIT_DIR, PROJECT_ROOT
from backend.app.database import init_db, SyncSessionLocal
from backend.app.services.seed_data import seed_database_sync
from backend.app.services.tripwire_service import tripwire_service

# Routers
from backend.app.routes.bom_routes import router as bom_router
from backend.app.routes.parts_routes import router as parts_router
from backend.app.routes.inspection_routes import router as inspection_router
from backend.app.routes.stream_routes import router as stream_router
from backend.app.routes.labeling_routes import router as labeling_router
from backend.app.routes.training_routes import router as training_router
from backend.app.routes.audit_routes import router as audit_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize SQLite Database Schema
    await init_db()
    print("[Main] SQLite database tables initialized.")

    # 2. Seed Default Sample BOM 31162814SD05076 & Global Parts Catalog
    with SyncSessionLocal() as sync_db:
        seed_database_sync(sync_db)
    print("[Main] Default Plant BOM (31162814SD05076) and Parts Catalog seeded.")

    # 3. Start default session with pre-seeded recipe
    try:
        tripwire_service.start_session(settings.active_master_code, operator_notes="Auto-loaded on startup")
        print(f"[Main] Active inspection session initialized for {settings.active_master_code}.")
    except Exception as e:
        print(f"[Main] Notice during initial session start: {e}")

    yield

    print("[Main] Shutting down vision inspector services.")

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Industrial Conveyor Belt BOM Verification, Auto-Labeling & YOLO26 Training System",
    lifespan=lifespan
)

# Enable CORS for local Vite dev server and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(bom_router)
app.include_router(parts_router)
app.include_router(inspection_router)
app.include_router(stream_router)
app.include_router(labeling_router)
app.include_router(training_router)
app.include_router(audit_router)

# Mount audit snapshots static directory
app.mount("/static_audit", StaticFiles(directory=str(STATIC_AUDIT_DIR)), name="static_audit")

# Mount Industrial SOP & User Manual HTML Project
manual_dir = PROJECT_ROOT / "manual"
if manual_dir.exists():
    app.mount("/manual", StaticFiles(directory=str(manual_dir), html=True), name="manual")

# Production: Mount frontend build if dist folder exists
frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def index():
        return {
            "app": settings.app_name,
            "version": settings.version,
            "status": "ONLINE",
            "active_recipe": settings.active_master_code,
            "frontend_note": "Frontend running on Vite dev server (http://localhost:5173) or run 'npm run build' in frontend/ to bundle single-port deployment."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
