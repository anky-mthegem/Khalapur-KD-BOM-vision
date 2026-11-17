"""
Labeling Studio Routes:
Capture conveyor frames, run OpenCV adaptive contour proposals, and save verified YOLO-OBB labels.
"""
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database import get_db
from backend.app.models.dataset import LabeledFrame
from backend.app.services.camera_service import camera_service
from backend.app.services.auto_labeler import auto_labeler

router = APIRouter(prefix="/api/labeling", tags=["Labeling Studio"])

class ContourProposalRequest(BaseModel):
    threshold_val: int = 60
    blur_kernel: int = 5
    min_area: int = 300
    max_area: int = 50000

class SaveAnnotationsRequest(BaseModel):
    annotations: List[Dict[str, Any]]
    master_item_code: Optional[str] = None

@router.post("/capture-frame")
async def capture_current_frame():
    """Captures current frame from camera for annotation."""
    frame = camera_service.get_latest_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="Camera frame not available.")
    
    # Run default contour proposal
    proposals = auto_labeler.auto_segment_contours(frame)
    
    # Encode as JPEG base64 or serve via stream
    ret, buffer = cv2.imencode(".jpg", frame)
    import base64
    b64_img = base64.b64encode(buffer).decode("utf-8")

    return {
        "image_base64": f"data:image/jpeg;base64,{b64_img}",
        "width": frame.shape[1],
        "height": frame.shape[0],
        "proposals": proposals
    }

@router.post("/auto-annotate")
async def generate_proposals(params: ContourProposalRequest):
    """Re-runs OpenCV adaptive contour analysis with customized slider parameters."""
    frame = camera_service.get_latest_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="Camera frame not available.")

    proposals = auto_labeler.auto_segment_contours(
        image=frame,
        threshold_val=params.threshold_val,
        blur_kernel=params.blur_kernel,
        min_area=params.min_area,
        max_area=params.max_area
    )
    return {"proposals": proposals}

@router.post("/save-annotations")
async def save_annotations(payload: SaveAnnotationsRequest):
    """Saves annotations to YOLO dataset format and increments catalog sample counts."""
    frame = camera_service.get_latest_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="No active camera frame to save.")

    result = auto_labeler.save_labeled_frame(
        image=frame,
        annotations=payload.annotations,
        master_item_code=payload.master_item_code
    )
    return {"status": "SAVED", "result": result}

@router.get("/frames")
async def list_labeled_frames(db: AsyncSession = Depends(get_db)):
    """Lists saved dataset frames."""
    res = await db.execute(select(LabeledFrame).order_by(LabeledFrame.created_at.desc()))
    frames = res.scalars().all()
    return [f.to_dict() for f in frames]
