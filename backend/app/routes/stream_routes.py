"""
Real-Time Video Streaming & WebSocket Event Broadcaster.
Streams MJPEG video with rendered OBB overlays and broadcasts live tripwire counts and hardware events via WebSocket.
"""
import cv2
import time
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Response, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

from backend.app.services.camera_service import camera_service
from backend.app.services.vision_engine import vision_engine
from backend.app.services.tripwire_service import tripwire_service
from backend.app.config import settings

router = APIRouter(tags=["Video Stream & WebSockets"])

active_connections: List[WebSocket] = []

class CameraSwitchRequest(BaseModel):
    mode: str = "USB"  # "USB", "RTSP"
    device_index: Optional[int] = 0
    path_or_index: Optional[Union[str, int]] = None
    width: Optional[int] = 1280
    height: Optional[int] = 720

async def broadcast_event(event_type: str, data: Any):
    payload = {"event": event_type, "data": data, "timestamp": time.time()}
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_json(payload)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in active_connections:
            active_connections.remove(ws)

def generate_mjpeg_stream():
    """Generates an annotated MJPEG multipart stream."""
    last_frame_time = time.time()
    
    while True:
        frame = camera_service.get_latest_frame()
        if frame is None:
            time.sleep(0.03)
            continue

        h, w = frame.shape[:2]

        # 1. Vision Engine inference & ByteTrack tracking
        annotated_frame, tracked_objects = vision_engine.process_frame(frame)

        # 2. Check Tripwire crossings & count increments
        cross_events = tripwire_service.check_tripwire_crossings(tracked_objects, w, h)
        if cross_events:
            # Broadcast crossing to UI WebSocket clients
            asyncio.run(broadcast_event("TRIPWIRE_CROSS", cross_events))
            asyncio.run(broadcast_event("STATE_UPDATE", tripwire_service.get_current_state()))

        # 3. Render Tripwire Overlay
        final_frame = tripwire_service.render_tripwire_overlay(annotated_frame)

        # 4. Encode as JPEG
        ret, buffer = cv2.imencode(".jpg", final_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

        # Frame rate throttle
        elapsed = time.time() - last_frame_time
        sleep_time = max(0.005, (1.0 / settings.target_fps) - elapsed)
        time.sleep(sleep_time)
        last_frame_time = time.time()

@router.get("/api/stream/mjpeg")
def video_feed():
    """MJPEG stream endpoint for conveyor viewport."""
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/api/stream/frame")
def single_frame():
    """Returns current pristine raw frame from camera."""
    frame = camera_service.get_latest_frame()
    if frame is None:
        return Response(status_code=503, content="Camera frame not ready")
    ret, buffer = cv2.imencode(".jpg", frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")

@router.get("/api/stream/devices")
def list_camera_devices(force_refresh: bool = Query(False, description="Force re-probing of hardware USB ports")):
    """Enumerates available physical USB cameras and active stream mode."""
    devices = camera_service.probe_available_cameras(max_indices=4, force=force_refresh)
    return {
        "current_mode": camera_service.mode,
        "current_index": camera_service.device_index,
        "source_type": camera_service.source_type,
        "is_connected": camera_service.is_connected,
        "devices": devices
    }

@router.get("/api/stream/status")
def get_stream_status():
    """Returns real-time status of active camera hardware."""
    return camera_service.get_status()

@router.post("/api/stream/source")
async def switch_camera_source(
    payload: Optional[CameraSwitchRequest] = None,
    mode: Optional[str] = None,
    path_or_index: Optional[Union[str, int]] = None
):
    """
    Switches camera source to chosen USB Camera device index or RTSP stream.
    Supports JSON body payload or URL query parameters.
    """
    target_mode = (payload.mode if payload and payload.mode else mode) or "USB"
    target_index = None
    if payload and payload.device_index is not None:
        target_index = payload.device_index
    elif payload and payload.path_or_index is not None:
        target_index = payload.path_or_index
    elif path_or_index is not None:
        target_index = path_or_index
    else:
        target_index = settings.camera_index

    width = payload.width if payload and payload.width else 1280
    height = payload.height if payload and payload.height else 720

    status = camera_service.init_source(
        mode=target_mode,
        path_or_index=target_index,
        width=width,
        height=height
    )

    # Broadcast source change to UI clients via WebSocket
    await broadcast_event("CAMERA_CHANGED", status)

    return {
        "status": "SOURCE_CHANGED",
        **status
    }

@router.websocket("/ws/inspection")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send initial inspection state and camera status
        await websocket.send_json({
            "event": "INIT_STATE",
            "data": tripwire_service.get_current_state(),
            "camera": camera_service.get_status()
        })
        while True:
            # Keepalive listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)
