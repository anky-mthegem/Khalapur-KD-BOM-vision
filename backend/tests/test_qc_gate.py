"""
Unit tests for 100% Match QC Gate Verification Logic.
"""
import pytest
from backend.app.services.tripwire_service import TripwireService

def test_qc_gate_blocked_when_missing_items():
    svc = TripwireService()
    svc.active_session_uid = "qc-test-session"
    svc.recipe_items = [
        {"sr_no": 1, "part_uid": "HOM196273", "item_name": "WOOD SCREW 3.5X15", "drawing_no": "HOM196273", "target_qty": 4, "is_vision_inspected": True},
        {"sr_no": 2, "part_uid": "CARTON_BOX", "item_name": "CARTON", "drawing_no": "—", "target_qty": 1, "is_vision_inspected": False}
    ]
    # Only 2 out of 4 counted
    svc.counts = {"HOM196273": 2, "CARTON_BOX": 0}

    result = svc.complete_batch()
    assert result["status"] == "BLOCKED"
    assert len(result["missing_items"]) == 1
    assert result["missing_items"][0]["drawing_no"] == "HOM196273"
    assert result["missing_items"][0]["missing_qty"] == 2
    assert result["qc_token"] is None

def test_qc_gate_passed_when_exact_match():
    svc = TripwireService()
    svc.active_session_uid = "qc-test-session-pass"
    svc.recipe_items = [
        {"sr_no": 1, "part_uid": "HOM196273", "item_name": "WOOD SCREW 3.5X15", "drawing_no": "HOM196273", "target_qty": 4, "is_vision_inspected": True},
        {"sr_no": 2, "part_uid": "CARTON_BOX", "item_name": "CARTON", "drawing_no": "—", "target_qty": 1, "is_vision_inspected": False}
    ]
    # Exact match for vision inspected item (carton is ignored for gate)
    svc.counts = {"HOM196273": 4, "CARTON_BOX": 0}

    result = svc.complete_batch()
    assert result["status"] == "PASSED"
    assert len(result["missing_items"]) == 0
    assert result["qc_token"] is not None
    assert result["qc_token"].startswith("QC-")
