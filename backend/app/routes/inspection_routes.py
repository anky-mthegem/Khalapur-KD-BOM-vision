"""
Inspection Session & Tripwire Management Routes.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from backend.app.schemas.session import InspectionStartRequest, TripwireConfig, CompleteBatchResponse
from backend.app.services.tripwire_service import tripwire_service
from backend.app.services.camera_service import camera_service
from backend.app.services.vision_engine import vision_engine

router = APIRouter(prefix="/api/inspection", tags=["Conveyor Inspection"])

@router.post("/start")
async def start_inspection_session(payload: InspectionStartRequest):
    """Initializes a new inspection session for a Master Item Code."""
    try:
        state = tripwire_service.start_session(payload.master_item_code, payload.operator_notes)
        return {"status": "SESSION_STARTED", "state": state}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/current")
async def get_current_session():
    """Returns the live state of the active inspection session and recipe counts."""
    return tripwire_service.get_current_state()

@router.post("/reset-counts")
async def reset_session_counts():
    """Resets current counted quantities back to 0 without ending the active session."""
    tripwire_service.reset_counts()
    return {"status": "RESET", "state": tripwire_service.get_current_state()}

@router.get("/tripwire")
async def get_tripwire_config():
    """Gets the current normalized tripwire coordinates and direction."""
    return tripwire_service.get_tripwire()

@router.put("/tripwire")
async def update_tripwire_config(config: TripwireConfig):
    """Updates the tripwire geometry."""
    tripwire_service.set_tripwire([config.x1, config.y1, config.x2, config.y2], config.direction)
    return {"status": "UPDATED", "tripwire": tripwire_service.get_tripwire()}

@router.post("/complete-batch", response_model=CompleteBatchResponse)
async def complete_batch_qc_gate():
    """
    100% Match QC Gate:
    Verifies that all is_vision_inspected items match the exact target quantity.
    Returns PASS or BLOCKED with missing item details and snapshot image.
    """
    snapshot = camera_service.get_latest_frame()
    if snapshot is not None:
        # Overlay detections and tripwire onto audit snapshot
        snapshot, _ = vision_engine.process_frame(snapshot)
        snapshot = tripwire_service.render_tripwire_overlay(snapshot)

    result = tripwire_service.complete_batch(snapshot)
    return result

@router.post("/simulate-crossing")
async def simulate_item_crossing(part_uid: str, item_name: str = "Simulated Part"):
    """
    Windows 11 Dev Utility: Injects a simulated fastener to cross the conveyor tripwire.
    """
    camera_service.trigger_simulated_item(part_uid, item_name)
    return {"status": "SIMULATED_ITEM_INJECTED", "part_uid": part_uid}
