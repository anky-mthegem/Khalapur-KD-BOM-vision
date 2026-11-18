"""
Global Parts Catalog Routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.parts import PartsCatalog
from backend.app.schemas.parts import PartResponse, PartUpdate

router = APIRouter(prefix="/api/parts", tags=["Global Parts Master"])

@router.get("", response_model=List[PartResponse])
async def list_parts(db: AsyncSession = Depends(get_db)):
    """Retrieves all parts registered in the global catalog."""
    res = await db.execute(select(PartsCatalog).order_by(PartsCatalog.yolo_class_id))
    parts = res.scalars().all()
    return parts

@router.get("/untrained", response_model=List[PartResponse])
async def list_untrained_parts(db: AsyncSession = Depends(get_db)):
    """Retrieves only parts requiring labeling samples or retraining."""
    res = await db.execute(
        select(PartsCatalog)
        .filter(PartsCatalog.training_status.in_(["UNTRAINED", "LABELED"]))
        .order_by(PartsCatalog.yolo_class_id)
    )
    return res.scalars().all()

@router.patch("/{part_uid}", response_model=PartResponse)
async def update_part(part_uid: str, payload: PartUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(PartsCatalog).filter_by(part_uid=part_uid))
    part = res.scalars().first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found.")

    if payload.item_name is not None:
        part.item_name = payload.item_name
    if payload.drawing_no is not None:
        part.drawing_no = payload.drawing_no.strip().upper()
        part.part_uid = payload.drawing_no.strip().upper()
    if payload.training_status is not None:
        part.training_status = payload.training_status

    await db.commit()
    await db.refresh(part)
    return part
