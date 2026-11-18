"""
Unit tests for 2D Tripwire Crossing Geometry and Debounce Logic.
"""
import pytest
from backend.app.services.tripwire_service import segments_intersect, ccw, TripwireService

def test_segments_intersect():
    # Perpendicular crossing
    A = (10.0, 50.0)
    B = (90.0, 50.0)
    C = (50.0, 10.0)
    D = (50.0, 90.0)
    assert segments_intersect(A, B, C, D) is True

    # Parallel non-intersecting
    E = (10.0, 20.0)
    F = (90.0, 20.0)
    assert segments_intersect(A, B, E, F) is False

    # Diagonal crossing
    G = (20.0, 20.0)
    H = (80.0, 80.0)
    I = (20.0, 80.0)
    J = (80.0, 20.0)
    assert segments_intersect(G, H, I, J) is True

def test_tripwire_crossing_and_debounce():
    svc = TripwireService()
    svc.set_tripwire([0.5, 0.0, 0.5, 1.0], direction="LEFT_TO_RIGHT")
    
    # Mock active session
    svc.active_session_uid = "test-session-123"
    svc.active_recipe_code = "31162814SD05076"
    svc.recipe_items = [
        {"sr_no": 1, "part_uid": "HOM196273", "item_name": "WOOD SCREW 3.5X15", "drawing_no": "HOM196273", "target_qty": 2, "is_vision_inspected": True}
    ]
    svc.counts = {"HOM196273": 0}
    svc.crossed_track_ids.clear()

    frame_w, frame_h = 1000, 1000
    # Tripwire is vertical at x = 500

    # Frame 1: Object approaches tripwire from left (x=450 to x=550)
    tracked_objects = [{
        "track_id": 99,
        "part_uid": "HOM196273",
        "item_name": "WOOD SCREW 3.5X15",
        "prev_centroid": (450.0, 500.0),
        "centroid": (550.0, 500.0)
    }]

    events = svc.check_tripwire_crossings(tracked_objects, frame_w, frame_h)
    assert len(events) == 1
    assert events[0]["track_id"] == 99
    assert events[0]["new_count"] == 1
    assert svc.counts["HOM196273"] == 1

    # Frame 2: Same object moves further (x=550 to x=650) -> Must NOT trigger again (debounced)
    tracked_objects_f2 = [{
        "track_id": 99,
        "part_uid": "HOM196273",
        "item_name": "WOOD SCREW 3.5X15",
        "prev_centroid": (550.0, 500.0),
        "centroid": (650.0, 500.0)
    }]
    events_f2 = svc.check_tripwire_crossings(tracked_objects_f2, frame_w, frame_h)
    assert len(events_f2) == 0
    assert svc.counts["HOM196273"] == 1

def test_simulate_crossing():
    svc = TripwireService()
    svc.active_session_uid = "test-session-sim"
    svc.counts = {"HOM196273": 1}
    svc.recipe_items = [
        {"id": 42, "sr_no": 1, "part_uid": "HOM196273", "item_name": "WOOD SCREW 3.5X15", "drawing_no": "HOM196273", "target_qty": 2, "is_vision_inspected": True}
    ]
    res = svc.simulate_crossing("HOM196273", "WOOD SCREW 3.5X15")
    assert res["new_count"] == 2
    assert svc.counts["HOM196273"] == 2

def test_sync_item_vision_inspection():
    svc = TripwireService()
    svc.recipe_items = [
        {"id": 101, "sr_no": 1, "part_uid": "HOM196273", "item_name": "WOOD SCREW", "drawing_no": "HOM196273", "target_qty": 2, "is_vision_inspected": True}
    ]
    svc.sync_item_vision_inspection(101, False)
    assert svc.recipe_items[0]["is_vision_inspected"] is False
    svc.sync_item_vision_inspection(101, True)
    assert svc.recipe_items[0]["is_vision_inspected"] is True
