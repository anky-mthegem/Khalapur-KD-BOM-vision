"""
Unit Tests for Hybrid Ultralytics ByteTrack & SimpleTracker Vision Engine.
Verifies multi-object tracking, Kalman/Euclidean trajectory persistence, and fallback resilience.
"""
import cv2
import numpy as np
import pytest
from backend.app.services.vision_engine import vision_engine, SimpleTracker
from backend.app.services.tripwire_service import segments_intersect

def test_simple_tracker_fallback():
    """Verify SimpleTracker assigns persistent track IDs across moving synthetic frames."""
    tracker = SimpleTracker(distance_threshold=80.0)

    # Frame 1: Object at (100, 100)
    det1 = [{
        "obb": [[90, 90], [110, 90], [110, 110], [90, 110]],
        "centroid": (100.0, 100.0),
        "class_id": 0,
        "part_uid": "HOM196273",
        "item_name": "HEX BOLT M6",
        "confidence": 0.95
    }]
    res1 = tracker.update(det1)
    assert len(res1) == 1
    tid1 = res1[0]["track_id"]
    assert res1[0]["centroid"] == (100.0, 100.0)

    # Frame 2: Same object moved along conveyor to (120, 100)
    det2 = [{
        "obb": [[110, 90], [130, 90], [130, 110], [110, 110]],
        "centroid": (120.0, 100.0),
        "class_id": 0,
        "part_uid": "HOM196273",
        "item_name": "HEX BOLT M6",
        "confidence": 0.96
    }]
    res2 = tracker.update(det2)
    assert len(res2) == 1
    assert res2[0]["track_id"] == tid1
    assert res2[0]["prev_centroid"] == (100.0, 100.0)
    assert res2[0]["centroid"] == (120.0, 100.0)

def test_vision_engine_process_frame_fallback():
    """Verify vision engine process_frame operates cleanly in optical fallback mode."""
    # Temporarily set model to None
    orig_model = vision_engine.model
    vision_engine.model = None

    # Synthetic frame with a bright rectangle on dark conveyor background
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.rectangle(frame, (300, 250), (450, 350), (200, 200, 200), -1)

    annotated, tracked = vision_engine.process_frame(frame)
    assert annotated is not None
    assert annotated.shape == (720, 1280, 3)
    assert isinstance(tracked, list)
    if tracked:
        assert "track_id" in tracked[0]
        assert "prev_centroid" in tracked[0]
        assert "centroid" in tracked[0]

    # Restore model
    vision_engine.model = orig_model

def test_vision_engine_ultralytics_bytetrack():
    """Verify Ultralytics ByteTrack operates with native model weights."""
    if vision_engine.model is not None:
        frame = np.zeros((640, 640, 3), dtype=np.uint8)
        annotated, tracked = vision_engine.process_frame(frame)
        assert annotated is not None
        assert isinstance(tracked, list)
        assert annotated.shape == (640, 640, 3)

def test_trajectory_tripwire_intersection():
    """Verify trajectory history (prev_centroid -> curr_centroid) correctly intersects tripwire line."""
    prev_c = (200.0, 300.0)
    curr_c = (400.0, 300.0)  # Moving left-to-right across x=300

    tripwire_p1 = (300.0, 100.0)
    tripwire_p2 = (300.0, 500.0)

    intersects = segments_intersect(prev_c, curr_c, tripwire_p1, tripwire_p2)
    assert intersects is True

def test_reset_tracking():
    """Verify reset_tracking cleans up state."""
    vision_engine.reset_tracking()
    assert len(vision_engine.track_history) == 0
    assert len(vision_engine.track_disappeared) == 0
