from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class TrainingStartRequest(BaseModel):
    base_model: str = "yolo26s-obb.pt"
    epochs: int = 50
    imgsz: int = 1280
    device: str = "auto"
    run_name: Optional[str] = None

class TrainingStatusResponse(BaseModel):
    status: str  # "IDLE", "RUNNING", "COMPLETED", "FAILED"
    run_name: Optional[str] = None
    current_epoch: int = 0
    total_epochs: int = 0
    loss: float = 0.0
    map50: float = 0.0
    map50_95: float = 0.0
    active_weights: str
    last_error: Optional[str] = None
    logs: Optional[list[str]] = []

class ModelActivateRequest(BaseModel):
    weights_path_or_name: str
