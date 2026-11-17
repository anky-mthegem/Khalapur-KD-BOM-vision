"""
Camera & Video Source Abstraction Layer.
Supports OpenCV physical camera / RTSP streams, mock video file playback,
and an autonomous synthetic conveyor simulator for Windows 11 offline testing.
"""
import cv2
import time
import threading
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from backend.app.config import settings, DEFAULT_MOCK_VIDEO, SAMPLE_DATA_DIR

class BaseCamera:
    def get_frame(self) -> Optional[np.ndarray]:
        raise NotImplementedError
    def release(self):
        pass

class OpenCVCamera(BaseCamera):
    def __init__(self, source: Any):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            print(f"[OpenCVCamera] Warning: Could not open camera source {source}")

    def get_frame(self) -> Optional[np.ndarray]:
        if not self.cap or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            # Loop if video file
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        if self.cap:
            self.cap.release()

class SyntheticConveyorCamera(BaseCamera):
    """
    Self-contained conveyor belt generator for Windows 11 offline dev/testing.
    Generates a realistic 1280x720 conveyor belt texture with moving hardware pieces
    (screws, dowels, plugs) that roll across the screen from left to right.
    """
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.belt_offset = 0
        self.lock = threading.RLock()
        self.last_time = time.time()
        
        # Simulated hardware items moving on belt
        self.simulated_items: List[Dict[str, Any]] = []
        self._init_items()

    def _init_items(self):
        # Initial cluster of fasteners
        parts = [
            ("HOM196273", "WOOD SCREW 3.5X15", (180, 180, 80), 40, 14, 25),
            ("HOM196276", "WOOD SCREW 3.5X15 PAN", (200, 200, 100), 42, 16, 65),
            ("HOM196277", "WOOD SCREW 3.5X20", (160, 190, 90), 50, 15, -30),
            ("HOM196280", "WOOD SCREW 4.0X35", (170, 170, 70), 70, 18, 45),
            ("HOM196328", "DUST PLUG D8", (210, 190, 150), 32, 28, 10),
            ("HOM196329", "DUST PLUG D5", (240, 240, 240), 24, 22, -15),
            ("HRD104875", "HINGE DOWEL CNS11", (120, 120, 180), 55, 20, 80),
            ("HRD104885", "METAL SUPPORT CNS20", (190, 190, 190), 45, 30, -45),
            ("HOM196306", "CORNER CONNECTOR", (140, 140, 140), 48, 48, 0),
            ("NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S", "M4 SLEEVE", (130, 160, 210), 60, 16, 15),
        ]
        
        x_stagger = 50
        for part_uid, name, color, length, width, angle in parts:
            self.simulated_items.append({
                "x": float(x_stagger),
                "y": float(np.random.randint(220, 500)),
                "length": length,
                "width": width,
                "angle": angle,
                "color": color,
                "part_uid": part_uid,
                "name": name,
                "speed": float(np.random.uniform(2.8, 3.8))
            })
            x_stagger -= 120

    def trigger_item(self, part_uid: str, item_name: str):
        """Allows test scripts to inject a specific part to cross the tripwire."""
        with self.lock:
            self.simulated_items.append({
                "x": 30.0,
                "y": float(np.random.randint(250, 480)),
                "length": 50,
                "width": 18,
                "angle": np.random.randint(-45, 45),
                "color": (200, 200, 200),
                "part_uid": part_uid,
                "name": item_name,
                "speed": 3.5
            })

    def get_frame(self) -> np.ndarray:
        with self.lock:
            now = time.time()
            dt = now - self.last_time
            self.last_time = now

            # 1. Base Conveyor Frame (Dark Industrial Matte Belt with Texture)
            frame = np.full((self.height, self.width, 3), 32, dtype=np.uint8)
            
            # Draw conveyor side rails
            cv2.rectangle(frame, (0, 0), (self.width, 100), (45, 48, 52), -1)
            cv2.rectangle(frame, (0, self.height - 100), (self.width, self.height), (45, 48, 52), -1)
            cv2.line(frame, (0, 100), (self.width, 100), (70, 75, 80), 2)
            cv2.line(frame, (0, self.height - 100), (self.width, self.height - 100), (70, 75, 80), 2)

            # Draw moving belt roller ribs
            self.belt_offset = (self.belt_offset + 3) % 80
            for x in range(-80 + self.belt_offset, self.width + 80, 80):
                cv2.line(frame, (x, 100), (x, self.height - 100), (38, 40, 44), 1)

            # 2. Render Simulated Hardware Fasteners
            for item in self.simulated_items:
                # Update position
                item["x"] += item["speed"]
                if item["x"] > self.width + 100:
                    # Recycle back to start
                    item["x"] = -100.0
                    item["y"] = float(np.random.randint(200, 520))

                # Draw rotated rectangle (fastener OBB)
                cx, cy = int(item["x"]), int(item["y"])
                if -60 <= cx <= self.width + 60:
                    rect = ((cx, cy), (item["length"], item["width"]), item["angle"])
                    box = cv2.boxPoints(rect)
                    box = np.int32(box)
                    cv2.fillPoly(frame, [box], item["color"])
                    cv2.polylines(frame, [box], True, (255, 255, 255), 1)
                    
                    # Inner detail (thread lines or head cross)
                    cv2.circle(frame, (cx, cy), 3, (40, 40, 40), -1)

            # Add subtle sensor noise and timestamp watermark
            cv2.putText(frame, f"CONVEYOR CAM [SIMULATED] | 1280x720 @ 30FPS | {time.strftime('%H:%M:%S')}",
                        (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 200), 2)

            return frame

class CameraService:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraService, cls).__new__(cls)
                cls._instance.camera = None
                cls._instance.source_type = "SYNTHETIC"
                cls._instance.active_frame = None
                cls._instance.is_running = False
                cls._instance._thread = None
                cls._instance.init_source(settings.camera_mode)
            return cls._instance

    def init_source(self, mode: str, path_or_index: Any = None):
        if self.camera:
            self.camera.release()

        if mode == "MOCK" or mode == "SYNTHETIC":
            if path_or_index and Path(path_or_index).exists():
                self.camera = OpenCVCamera(str(path_or_index))
                self.source_type = f"FILE: {Path(path_or_index).name}"
            else:
                self.camera = SyntheticConveyorCamera()
                self.source_type = "SYNTHETIC_CONVEYOR"
        elif mode == "RTSP":
            self.camera = OpenCVCamera(path_or_index or settings.rtsp_url)
            self.source_type = "RTSP"
        elif mode == "USB":
            idx = int(path_or_index) if path_or_index is not None else settings.camera_index
            self.camera = OpenCVCamera(idx)
            self.source_type = f"USB_CAM_{idx}"
        else:
            self.camera = SyntheticConveyorCamera()
            self.source_type = "SYNTHETIC_CONVEYOR"

        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()

    def _capture_loop(self):
        while self.is_running:
            if self.camera:
                frame = self.camera.get_frame()
                if frame is not None:
                    self.active_frame = frame
            time.sleep(1.0 / settings.target_fps)

    def get_latest_frame(self) -> Optional[np.ndarray]:
        return self.active_frame.copy() if self.active_frame is not None else None

    def trigger_simulated_item(self, part_uid: str, item_name: str):
        if isinstance(self.camera, SyntheticConveyorCamera):
            self.camera.trigger_item(part_uid, item_name)

camera_service = CameraService()
