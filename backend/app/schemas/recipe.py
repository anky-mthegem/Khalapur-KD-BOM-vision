from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RecipeItemBase(BaseModel):
    sr_no: int
    part_uid: str
    item_name: str
    drawing_no: Optional[str] = "—"
    target_qty: int
    is_vision_inspected: bool = True

class RecipeItemResponse(RecipeItemBase):
    id: int
    recipe_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RecipeBase(BaseModel):
    master_item_code: str
    description: str
    total_items: int
    vision_items_count: int

class RecipeResponse(RecipeBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[RecipeItemResponse] = []

    class Config:
        from_attributes = True

class BomPreviewItem(BaseModel):
    sr_no: int
    part_uid: str
    item_name: str
    drawing_no: str
    target_qty: int
    is_vision_inspected: bool
    is_new_part: bool
    training_status: str

class BomPreviewResponse(BaseModel):
    master_item_code: str
    description: str
    sheet_name: str
    total_items: int
    vision_items_count: int
    excluded_packaging_count: int
    new_parts_count: int
    items: List[BomPreviewItem]

class BomCommitRequest(BaseModel):
    master_item_code: str
    description: str
    items: List[RecipeItemBase]
