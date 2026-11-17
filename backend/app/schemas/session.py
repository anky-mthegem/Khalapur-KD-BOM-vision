from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SessionCountItem(BaseModel):
    part_uid: str
    target_qty: int
    counted_qty: int
    status: str
    last_counted_at: Optional[datetime] = None

class InspectionStartRequest(BaseModel):
    master_item_code: str
    operator_notes: Optional[str] = None

class TripwireConfig(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    direction: str = "LEFT_TO_RIGHT"

class CompleteBatchResponse(BaseModel):
    status: str  # "PASSED" or "BLOCKED"
    session_uid: str
    total_target: int
    total_counted: int
    missing_items: List[dict] = []
    overcounted_items: List[dict] = []
    snapshot_url: Optional[str] = None
    qc_token: Optional[str] = None
    message: str
