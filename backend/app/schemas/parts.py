from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PartBase(BaseModel):
    part_uid: str
    item_name: str
    drawing_no: Optional[str] = None
    yolo_class_id: int
    training_status: str = "UNTRAINED"
    sample_count: int = 0

class PartResponse(PartBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PartUpdate(BaseModel):
    item_name: Optional[str] = None
    drawing_no: Optional[str] = None
    training_status: Optional[str] = None
