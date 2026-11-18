"""
Labeling Studio Routes:
Capture conveyor frames, run OpenCV adaptive contour proposals, and save verified YOLO-OBB labels.
"""
import cv2
import base64
import numpy as np
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.config import DATASETS_DIR
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
    image_base64: Optional[str] = None

class SaveAnnotationsRequest(BaseModel):
    annotations: List[Dict[str, Any]]
    master_item_code: Optional[str] = None

class SaveComponentRequest(BaseModel):
    image_base64: str
    item_name: Optional[str] = None
    drawing_no: Optional[str] = None
    polygon: Optional[List[List[float]]] = None
    master_item_code: Optional[str] = None
    regions: Optional[List[Dict[str, Any]]] = None

@router.post("/upload-image")
async def upload_image_file(file: UploadFile = File(...)):
    """
    Accepts an uploaded component image (from user's Browse button),
    decodes it, and returns base64 and dimensions.
    Starts with clean empty proposals so the operator can draw boxes manually
    or click 'Auto Box' on demand.
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file or format.")

    ret, buffer = cv2.imencode(".jpg", image)
    b64_img = base64.b64encode(buffer).decode("utf-8")

    return {
        "filename": file.filename,
        "image_base64": f"data:image/jpeg;base64,{b64_img}",
        "width": image.shape[1],
        "height": image.shape[0],
        "proposals": []
    }

@router.post("/save-component")
async def save_component(payload: SaveComponentRequest):
    """
    Saves an annotated component image directly into the YOLO training folder,
    using the item_name from the plant BOM as the class label.
    """
    # Extract raw base64 data
    b64_data = payload.image_base64
    if "," in b64_data:
        b64_data = b64_data.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(b64_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Decoded image is empty.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode base64 image: {e}")

    annotations = []
    if payload.regions and len(payload.regions) > 0:
        for r in payload.regions:
            annotations.append({
                "item_name": r.get("item_name") or payload.item_name,
                "part_uid": r.get("part_uid") or r.get("drawing_no") or payload.drawing_no or r.get("item_name"),
                "polygon": r.get("polygon"),
                "is_browse_upload": True
            })
    elif payload.item_name:
        annotation = {
            "item_name": payload.item_name,
            "part_uid": payload.drawing_no if payload.drawing_no and payload.drawing_no != "—" else payload.item_name,
            "polygon": payload.polygon or [[0.05, 0.05], [0.95, 0.05], [0.95, 0.95], [0.05, 0.95]],
            "is_browse_upload": True
        }
        annotations.append(annotation)
    else:
        raise HTTPException(status_code=400, detail="Missing item_name or regions in save request.")

    result = auto_labeler.save_labeled_frame(
        image=image,
        annotations=annotations,
        master_item_code=payload.master_item_code
    )

    return {
        "status": "SAVED",
        "regions_saved": len(annotations),
        "result": result
    }

@router.get("/dataset-summary")
async def get_dataset_summary():
    """
    Retrieves the complete breakdown of images stored in the training folder
    and sample counts per BOM item_name.
    """
    return auto_labeler.get_dataset_summary()

@router.delete("/sample/{stem}")
async def delete_dataset_sample(stem: str):
    """
    Deletes a sample image and label from the training folder.
    """
    img_path_jpg = DATASETS_DIR / "images" / "train" / f"{stem}.jpg"
    img_path_png = DATASETS_DIR / "images" / "train" / f"{stem}.png"
    lbl_path = DATASETS_DIR / "labels" / "train" / f"{stem}.txt"

    deleted = False
    for p in [img_path_jpg, img_path_png, lbl_path]:
        if p.exists():
            p.unlink()
            deleted = True

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Sample '{stem}' not found.")

    return {"status": "DELETED", "stem": stem}

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
    """Re-runs OpenCV adaptive contour analysis on uploaded image or camera frame."""
    image = None
    if params.image_base64:
        b64_data = params.image_base64
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        try:
            img_bytes = base64.b64decode(b64_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode base64 image: {e}")

    if image is None:
        image = camera_service.get_latest_frame()

    if image is None:
        raise HTTPException(status_code=503, detail="No active image or camera frame available for auto-contour.")

    proposals = auto_labeler.auto_segment_contours(
        image=image,
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
