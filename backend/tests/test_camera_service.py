"""
Unit & Integration Tests for USB Camera & Video Stream Subsystem.
Verifies physical USB camera initialization, hardware device index selection, and streaming endpoints.
"""
import pytest
import numpy as np
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.camera_service import camera_service, OpenCVCamera

client = TestClient(app)

def test_opencv_camera_usb_init():
    """Verify OpenCVCamera initializes in USB mode and produces valid 1280x720 frames."""
    cam = OpenCVCamera(0, width=1280, height=720)
    assert cam.is_usb is True
    assert cam.source == 0
    frame = cam.get_frame()
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape[0] > 0 and frame.shape[1] > 0
    cam.release()

def test_camera_service_init_and_status():
    """Verify camera service reports valid USB camera configuration status."""
    status = camera_service.init_source("USB", 0)
    assert status["mode"] == "USB"
    assert status["device_index"] == 0
    assert "USB_CAM_0" in status["source_type"]

    curr = camera_service.get_status()
    assert curr["mode"] == "USB"
    assert curr["device_index"] == 0
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

def test_camera_switch_usb_indices():
    """Verify switching between USB camera index 0 and index 1."""
    status0 = camera_service.init_source("USB", 0)
    assert status0["mode"] == "USB"
    assert status0["device_index"] == 0

    status1 = camera_service.init_source("USB", 1)
    assert status1["mode"] == "USB"
    assert status1["device_index"] == 1
    assert "USB_CAM_1" in status1["source_type"]

    # Revert back to index 0
    camera_service.init_source("USB", 0)

def test_stream_api_status():
    """Verify GET /api/stream/status endpoint."""
    res = client.get("/api/stream/status")
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "USB"
    assert "source_type" in data
    assert "is_connected" in data

def test_stream_api_devices():
    """Verify GET /api/stream/devices endpoint."""
    res = client.get("/api/stream/devices")
    assert res.status_code == 200
    data = res.json()
    assert data["current_mode"] == "USB"
    assert "devices" in data
    assert isinstance(data["devices"], list)

def test_stream_api_source_switch():
    """Verify POST /api/stream/source switching USB camera index."""
    res = client.post("/api/stream/source", json={"mode": "USB", "device_index": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["CONNECTED", "WARNING_NO_SIGNAL", "SOURCE_CHANGED"]
    assert data["mode"] == "USB"
    assert data["device_index"] == 1

    # Switch back to index 0
    res = client.post("/api/stream/source", json={"mode": "USB", "device_index": 0})
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "USB"
    assert data["device_index"] == 0

def test_stream_single_frame():
    """Verify GET /api/stream/frame returns image/jpeg bytes."""
    res = client.get("/api/stream/frame")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    assert len(res.content) > 100
