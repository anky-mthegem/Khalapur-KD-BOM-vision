"""
Inspection Audit Logs & QC Snapshot Routes.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from backend.app.database import get_db
from backend.app.models.session import InspectionSession
from backend.app.config import STATIC_AUDIT_DIR

router = APIRouter(prefix="/api/audit", tags=["Audit & Quality Control"])

@router.get("/logs")
async def get_audit_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Retrieves paginated audit logs of past inspection sessions."""
    res = await db.execute(
        select(InspectionSession).order_by(InspectionSession.start_time.desc()).limit(limit)
    )
    sessions = res.scalars().all()
    return [s.to_dict() for s in sessions]

@router.get("/snapshots/{filename}")
async def get_audit_snapshot(filename: str):
    """Serves recorded inspection snapshot images."""
    file_path = STATIC_AUDIT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Snapshot not found.")
    return FileResponse(str(file_path), media_type="image/jpeg")
