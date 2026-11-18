"""
Unit & Integration Tests for USB Camera & Video Stream Subsystem.
Verifies hardware device index selection, synthetic conveyor fallback, and stream switching endpoints.
"""
import pytest
import numpy as np
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.camera_service import camera_service, OpenCVCamera, SyntheticConveyorCamera

client = TestClient(app)

def test_synthetic_camera_generation():
    """Verify autonomous synthetic camera creates valid 1280x720 RGB frames."""
    cam = SyntheticConveyorCamera(width=1280, height=720)
    frame = cam.get_frame()
    assert frame is not None
    assert frame.shape == (720, 1280, 3)
    assert isinstance(frame, np.ndarray)
    cam.release()

def test_camera_service_init_and_status():
    """Verify camera service reports valid configuration status."""
    status = camera_service.init_source("SYNTHETIC")
    assert status["mode"] == "SYNTHETIC"
    assert status["source_type"] == "SYNTHETIC_CONVEYOR"
    assert status["is_connected"] is True

    curr = camera_service.get_status()
    assert curr["mode"] == "SYNTHETIC"
    assert "resolution" in curr
    assert curr["target_fps"] > 0

def test_camera_device_probing():
    """Verify hardware device probe returns a non-empty device list with index properties."""
    devices = camera_service.probe_available_cameras(max_indices=2, force=True)
    assert isinstance(devices, list)
    assert len(devices) > 0
    dev0 = devices[0]
    assert "index" in dev0
    assert "name" in dev0
    assert "available" in dev0

def test_camera_switch_to_usb_and_synthetic():
    """Verify switching to USB index 0 and back to Synthetic."""
    usb_status = camera_service.init_source("USB", 0)
    assert usb_status["mode"] == "USB"
    assert usb_status["device_index"] == 0
    assert "USB_CAM_0" in usb_status["source_type"]

    # Revert to synthetic
    synth_status = camera_service.init_source("SYNTHETIC")
    assert synth_status["mode"] == "SYNTHETIC"
    assert synth_status["source_type"] == "SYNTHETIC_CONVEYOR"

def test_stream_api_status():
    """Verify GET /api/stream/status endpoint."""
    res = client.get("/api/stream/status")
    assert res.status_code == 200
    data = res.json()
    assert "mode" in data
    assert "source_type" in data
    assert "is_connected" in data

def test_stream_api_devices():
    """Verify GET /api/stream/devices endpoint."""
    res = client.get("/api/stream/devices")
    assert res.status_code == 200
    data = res.json()
    assert "current_mode" in data
    assert "devices" in data
    assert isinstance(data["devices"], list)

def test_stream_api_source_switch():
    """Verify POST /api/stream/source switching between USB and Synthetic."""
    # Switch to USB index 0
    res = client.post("/api/stream/source", json={"mode": "USB", "device_index": 0})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["CONNECTED", "SOURCE_CHANGED"]
    assert data["mode"] == "USB"
    assert data["device_index"] == 0

    # Switch back to Synthetic
    res = client.post("/api/stream/source", json={"mode": "SYNTHETIC"})
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SYNTHETIC"

def test_stream_single_frame():
    """Verify GET /api/stream/frame returns image/jpeg bytes."""
    camera_service.init_source("SYNTHETIC")
    res = client.get("/api/stream/frame")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    assert len(res.content) > 100
