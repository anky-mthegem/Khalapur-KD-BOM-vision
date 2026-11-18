"""
Camera & Video Source Abstraction Layer.
Supports OpenCV physical USB cameras (with device index selection), RTSP streams,
mock video file playback, and an autonomous synthetic conveyor simulator for Windows 11 offline testing.
"""
import cv2
import time
import platform
import threading
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List, Union
from backend.app.config import settings, DEFAULT_MOCK_VIDEO, SAMPLE_DATA_DIR

class BaseCamera:
    def get_frame(self) -> Optional[np.ndarray]:
        raise NotImplementedError
    def release(self):
        pass

class OpenCVCamera(BaseCamera):
    """
    Hardware USB camera / RTSP / Video file wrapper using OpenCV.
    Provides fast DirectShow / native capture with zero-latency buffer settings,
    automatic reconnection attempts, and an industrial diagnostic fallback overlay.
    """
    def __init__(self, source: Any, width: int = 1280, height: int = 720):
        self.raw_source = source
        self.width = width
        self.height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened = False
        self.is_usb = False
        self.is_video_file = False
        self.actual_width = width
        self.actual_height = height

        # Convert string digit to int (e.g. "0" -> 0)
        if isinstance(source, str) and source.strip().isdigit():
            self.source = int(source.strip())
        else:
            self.source = source

        if isinstance(self.source, int):
            self.is_usb = True
        elif isinstance(self.source, str) and not self.source.startswith("rtsp://") and not self.source.startswith("http://"):
            self.is_video_file = True

        self._open_capture()

    def _open_capture(self):
        try:
            if self.is_usb:
                # Prefer DirectShow on Windows for fast USB enumeration & low latency
                backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
                self.cap = cv2.VideoCapture(self.source, backend)
                if not self.cap.isOpened() and backend != cv2.CAP_ANY:
                    self.cap = cv2.VideoCapture(self.source)

                if self.cap and self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_FPS, settings.target_fps)
                    self.is_opened = True
                    # Query actual dimensions
                    w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or self.width)
                    h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or self.height)
                    self.actual_width = w
                    self.actual_height = h
                else:
                    self.is_opened = False
                    print(f"[OpenCVCamera] Warning: Could not open USB camera at index {self.source}")
            else:
                self.cap = cv2.VideoCapture(self.source)
                self.is_opened = bool(self.cap and self.cap.isOpened())
                if self.is_opened:
                    w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or self.width)
                    h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or self.height)
                    self.actual_width = w
                    self.actual_height = h
        except Exception as e:
            print(f"[OpenCVCamera] Exception opening source {self.source}: {e}")
            self.is_opened = False

    def get_frame(self) -> np.ndarray:
        if not self.cap or not self.is_opened:
            return self._generate_diagnostic_frame("CAMERA NOT DETECTED / PORT BUSY")

        ret, frame = self.cap.read()
        if not ret or frame is None:
            if self.is_video_file:
                # Loop video file
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    return frame
            return self._generate_diagnostic_frame("NO VIDEO SIGNAL - CHECK USB CONNECTION")
        return frame

    def _generate_diagnostic_frame(self, message: str) -> np.ndarray:
        """Industrial diagnostic frame displayed when camera is unplugged or unavailable."""
        h = self.height or 720
        w = self.width or 1280
        frame = np.full((h, w, 3), 24, dtype=np.uint8)
        
        # Hazard stripe border
        cv2.rectangle(frame, (40, 40), (w - 40, h - 40), (45, 52, 175), 3)
        cv2.putText(frame, "LIVE CAMERA FEED: STANDBY", (w // 2 - 250, h // 2 - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
        cv2.putText(frame, message, (w // 2 - 280, h // 2 + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        source_desc = f"Selected Source: USB Camera Index [{self.source}]" if self.is_usb else f"Selected Source: {self.source}"
        cv2.putText(frame, f"{source_desc} | Use Ribbon 'Camera Settings' to switch index",
                    (w // 2 - 340, h // 2 + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        return frame

    def release(self):
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                print(f"[OpenCVCamera] Error during release: {e}")
        self.cap = None
        self.is_opened = False

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
        self.is_opened = True
        
        # Simulated hardware items moving on belt
        self.simulated_items: List[Dict[str, Any]] = []
        self._init_items()

    def _init_items(self):
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
                item["x"] += item["speed"]
                if item["x"] > self.width + 100:
                    item["x"] = -100.0
                    item["y"] = float(np.random.randint(200, 520))

                cx, cy = int(item["x"]), int(item["y"])
                if -60 <= cx <= self.width + 60:
                    rect = ((cx, cy), (item["length"], item["width"]), item["angle"])
                    box = cv2.boxPoints(rect)
                    box = np.int32(box)
                    cv2.fillPoly(frame, [box], item["color"])
                    cv2.polylines(frame, [box], True, (255, 255, 255), 1)
                    cv2.circle(frame, (cx, cy), 3, (40, 40, 40), -1)

            cv2.putText(frame, f"CONVEYOR CAM [SIMULATED] | 1280x720 @ 30FPS | {time.strftime('%H:%M:%S')}",
                        (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 200), 2)

            return frame

    def release(self):
        pass

class CameraService:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraService, cls).__new__(cls)
                cls._instance.camera = None
                cls._instance.mode = "SYNTHETIC"
                cls._instance.device_index = 0
                cls._instance.source_type = "SYNTHETIC_CONVEYOR"
                cls._instance.is_connected = True
                cls._instance.width = 1280
                cls._instance.height = 720
                cls._instance.active_frame = None
                cls._instance.is_running = False
                cls._instance._thread = None
                cls._instance._cached_devices = []
                cls._instance._last_probe_time = 0.0
                cls._instance.init_source(settings.camera_mode, settings.camera_index)
            return cls._instance

    def init_source(self, mode: str, path_or_index: Any = None, width: int = 1280, height: int = 720) -> Dict[str, Any]:
        """
        Dynamically switches video input source:
        - "USB": Physical USB camera by index (0, 1, 2, ...)
        - "SYNTHETIC" or "MOCK": Internal conveyor simulator or video file
        - "RTSP": Remote IP stream
        """
        with self._lock:
            self.width = width
            self.height = height

            # Cleanly release existing camera
            if self.camera:
                self.camera.release()
                self.camera = None
                # Brief pause for OS USB driver release
                time.sleep(0.1)

            mode_upper = (mode or "SYNTHETIC").strip().upper()

            if mode_upper == "USB":
                if path_or_index is not None and str(path_or_index).strip().isdigit():
                    idx = int(str(path_or_index).strip())
                else:
                    idx = settings.camera_index
                self.device_index = idx
                self.mode = "USB"
                settings.camera_index = idx
                settings.camera_mode = "USB"
                self.camera = OpenCVCamera(idx, width=width, height=height)
                self.source_type = f"USB_CAM_{idx}"
                self.is_connected = getattr(self.camera, "is_opened", False)

            elif mode_upper in ["MOCK", "SYNTHETIC"]:
                if path_or_index and Path(str(path_or_index)).exists():
                    self.camera = OpenCVCamera(str(path_or_index), width=width, height=height)
                    self.source_type = f"FILE: {Path(str(path_or_index)).name}"
                    self.mode = "FILE"
                else:
                    self.camera = SyntheticConveyorCamera(width=width, height=height)
                    self.source_type = "SYNTHETIC_CONVEYOR"
                    self.mode = "SYNTHETIC"
                    settings.camera_mode = "SYNTHETIC"
                self.is_connected = True

            elif mode_upper == "RTSP":
                url = str(path_or_index or settings.rtsp_url)
                self.camera = OpenCVCamera(url, width=width, height=height)
                self.source_type = "RTSP"
                self.mode = "RTSP"
                settings.camera_mode = "RTSP"
                self.is_connected = getattr(self.camera, "is_opened", False)

            else:
                self.camera = SyntheticConveyorCamera(width=width, height=height)
                self.source_type = "SYNTHETIC_CONVEYOR"
                self.mode = "SYNTHETIC"
                self.is_connected = True

            if not self.is_running:
                self.is_running = True
                self._thread = threading.Thread(target=self._capture_loop, daemon=True)
                self._thread.start()

            return self.get_status()

    def _capture_loop(self):
        while self.is_running:
            if self.camera:
                frame = self.camera.get_frame()
                if frame is not None:
                    self.active_frame = frame
            time.sleep(1.0 / settings.target_fps)

    def get_latest_frame(self) -> Optional[np.ndarray]:
        return self.active_frame.copy() if self.active_frame is not None else None

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of active camera hardware."""
        with self._lock:
            act_w = getattr(self.camera, "actual_width", self.width)
            act_h = getattr(self.camera, "actual_height", self.height)
            return {
                "status": "CONNECTED" if self.is_connected else "WARNING_NO_SIGNAL",
                "mode": self.mode,
                "device_index": self.device_index,
                "source_type": self.source_type,
                "is_connected": self.is_connected,
                "resolution": f"{act_w}x{act_h}",
                "target_fps": settings.target_fps
            }

    def probe_available_cameras(self, max_indices: int = 4, force: bool = False) -> List[Dict[str, Any]]:
        """
        Scans for available USB camera devices on host system.
        Caches results to avoid latency on repeated calls.
        """
        with self._lock:
            now = time.time()
            if not force and self._cached_devices and (now - self._last_probe_time < 30.0):
                return self._cached_devices

            devices = []
            backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
            current_usb_idx = self.device_index if self.mode == "USB" else None

            for idx in range(max_indices):
                if idx == current_usb_idx and self.camera and getattr(self.camera, "is_opened", False):
                    # Current active camera is verified already open and functioning
                    w = getattr(self.camera, "actual_width", self.width)
                    h = getattr(self.camera, "actual_height", self.height)
                    devices.append({
                        "index": idx,
                        "name": f"USB Camera {idx} (Active)",
                        "resolution": f"{w}x{h}",
                        "available": True,
                        "is_current": True
                    })
                    continue

                try:
                    cap = cv2.VideoCapture(idx, backend)
                    if not cap.isOpened() and backend != cv2.CAP_ANY:
                        cap = cv2.VideoCapture(idx)

                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            h, w = frame.shape[:2]
                            devices.append({
                                "index": idx,
                                "name": f"USB Camera {idx}",
                                "resolution": f"{w}x{h}",
                                "available": True,
                                "is_current": (idx == current_usb_idx)
                            })
                        cap.release()
                except Exception as e:
                    print(f"[CameraService] Probe error index {idx}: {e}")

            # If no physical cameras detected, include at least index 0 as placeholder option
            if not devices:
                devices.append({
                    "index": 0,
                    "name": "USB Camera 0 (Not Connected)",
                    "resolution": "1280x720",
                    "available": False,
                    "is_current": (self.device_index == 0)
                })

            self._cached_devices = devices
            self._last_probe_time = now
            return devices

    def trigger_simulated_item(self, part_uid: str, item_name: str):
        if isinstance(self.camera, SyntheticConveyorCamera):
            self.camera.trigger_item(part_uid, item_name)

camera_service = CameraService()
