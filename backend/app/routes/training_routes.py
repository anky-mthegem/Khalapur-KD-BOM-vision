"""
YOLO26-OBB Training & Model Hot-Swap Routes.
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from backend.app.database import get_db
from backend.app.models.training import TrainingRun
from backend.app.schemas.training import TrainingStartRequest, TrainingStatusResponse, ModelActivateRequest
from backend.app.services.training_service import training_service
from backend.app.config import WEIGHTS_DIR

router = APIRouter(prefix="/api/training", tags=["Model Training"])

@router.post("/start")
async def start_training_run(payload: TrainingStartRequest):
    """Starts background YOLO26-OBB training job."""
    res = training_service.start_training(
        base_model=payload.base_model,
        epochs=payload.epochs,
        imgsz=payload.imgsz,
        device=payload.device,
        run_name=payload.run_name
    )
    return res

@router.get("/status", response_model=TrainingStatusResponse)
async def get_training_status():
    """Retrieves live training status, epoch progress, and loss metrics."""
    return training_service.get_status()

@router.post("/activate")
async def activate_model(payload: ModelActivateRequest):
    """Hot-swaps trained weights into the live vision engine without restarting."""
    try:
        res = training_service.activate_model(payload.weights_path_or_name)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/models")
async def list_available_models():
    """Lists all available model weight files in models/weights."""
    weights = list(WEIGHTS_DIR.glob("*.pt"))
    return [
        {
            "filename": w.name,
            "path": str(w),
            "size_mb": round(w.stat().st_size / (1024 * 1024), 2) if w.exists() else 0,
            "is_active": w.name == training_service.current_status.get("active_weights")
        }
        for w in weights
    ]
