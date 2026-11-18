"""
Camera & Video Source Abstraction Layer.
Dedicated to real-time physical USB cameras (with device index selection) and RTSP streams.
Pure hardware-driven video acquisition with DirectShow low-latency capture on Windows.
"""
import cv2
import time
import platform
import threading
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List, Union
from backend.app.config import settings

class BaseCamera:
    def get_frame(self) -> Optional[np.ndarray]:
        raise NotImplementedError
    def release(self):
        pass

class OpenCVCamera(BaseCamera):
    """
    Hardware USB camera / RTSP stream wrapper using OpenCV.
    Provides fast DirectShow / native capture with zero-latency buffer settings,
    automatic reconnection attempts, and an industrial diagnostic fallback overlay.
    """
    def __init__(self, source: Any, width: int = 1280, height: int = 720):
        self._lock = threading.Lock()
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

        with self._lock:
            self._open_capture()

    def _open_capture(self):
        try:
            if self.is_usb:
                # DirectShow on Windows gives instantaneous camera capture without MSMF delay
                backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
                self.cap = cv2.VideoCapture(self.source, backend)
                if not self.cap.isOpened() and platform.system() != "Windows":
                    self.cap = cv2.VideoCapture(self.source)

                if self.cap and self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_FPS, settings.target_fps)
                    self.is_opened = True
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
        with self._lock:
            if not self.cap or not self.is_opened:
                return self._generate_diagnostic_frame("CAMERA NOT DETECTED / PORT BUSY")

            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    if self.is_video_file:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            return frame
                    return self._generate_diagnostic_frame("NO VIDEO SIGNAL - CHECK USB CONNECTION")
                return frame
            except Exception:
                return self._generate_diagnostic_frame("CAMERA BUSY / RECONNECTING")

    def _generate_diagnostic_frame(self, message: str) -> np.ndarray:
        """Industrial diagnostic frame displayed when camera is unplugged or unavailable."""
        h = self.height or 720
        w = self.width or 1280
        frame = np.full((h, w, 3), 20, dtype=np.uint8)
        
        cv2.rectangle(frame, (40, 40), (w - 40, h - 40), (45, 52, 175), 3)
        cv2.putText(frame, "LIVE CAMERA FEED: NO SIGNAL", (w // 2 - 260, h // 2 - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        cv2.putText(frame, message, (w // 2 - 280, h // 2 + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        source_desc = f"Selected Source: USB Camera Index [{self.source}]" if self.is_usb else f"Selected Source: {self.source}"
        cv2.putText(frame, f"{source_desc} | Select another index from 'Camera Source' in toolbar",
                    (w // 2 - 340, h // 2 + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        return frame

    def release(self):
        with self._lock:
            if self.cap:
                try:
                    self.cap.release()
                except Exception as e:
                    print(f"[OpenCVCamera] Error during release: {e}")
            self.cap = None
            self.is_opened = False

class CameraService:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraService, cls).__new__(cls)
                cls._instance.camera = None
                cls._instance.mode = "USB"
                cls._instance.device_index = settings.camera_index
                cls._instance.source_type = f"USB_CAM_{settings.camera_index}"
                cls._instance.is_connected = False
                cls._instance.width = 1280
                cls._instance.height = 720
                cls._instance.active_frame = None
                cls._instance.is_running = False
                cls._instance._thread = None
                cls._instance._cached_devices = []
                cls._instance._last_probe_time = 0.0
                cls._instance.init_source("USB", settings.camera_index)
            return cls._instance

    def init_source(self, mode: str = "USB", path_or_index: Any = None, width: int = 1280, height: int = 720) -> Dict[str, Any]:
        """
        Dynamically connects to physical USB camera hardware by device index (0, 1, 2, ...),
        or an RTSP/IP camera stream.
        """
        with self._lock:
            self.width = width
            self.height = height

            # Cleanly release existing camera
            if self.camera:
                self.camera.release()
                self.camera = None
                time.sleep(0.1)

            mode_upper = (mode or "USB").strip().upper()

            if mode_upper == "RTSP":
                url = str(path_or_index or settings.rtsp_url)
                self.camera = OpenCVCamera(url, width=width, height=height)
                self.source_type = "RTSP"
                self.mode = "RTSP"
                settings.camera_mode = "RTSP"
                self.is_connected = getattr(self.camera, "is_opened", False)
            else:
                # Default is always USB camera
                if path_or_index is not None and str(path_or_index).strip().isdigit():
                    idx = int(str(path_or_index).strip())
                elif isinstance(path_or_index, int):
                    idx = path_or_index
                else:
                    idx = settings.camera_index

                self.device_index = idx
                self.mode = "USB"
                settings.camera_index = idx
                settings.camera_mode = "USB"
                self.camera = OpenCVCamera(idx, width=width, height=height)
                self.source_type = f"USB_CAM_{idx}"
                self.is_connected = getattr(self.camera, "is_opened", False)

            if not self.is_running:
                self.is_running = True
                self._thread = threading.Thread(target=self._capture_loop, daemon=True)
                self._thread.start()

            return self.get_status()

    def stop(self):
        """Stops background capture thread and releases camera hardware."""
        with self._lock:
            self.is_running = False
            if self.camera:
                try:
                    self.camera.release()
                except Exception:
                    pass
                self.camera = None
            self.is_connected = False
            time.sleep(0.05)

    def _capture_loop(self):
        while self.is_running:
            try:
                if self.camera:
                    frame = self.camera.get_frame()
                    if frame is not None:
                        self.active_frame = frame
            except Exception:
                pass
            time.sleep(1.0 / settings.target_fps)

    def get_latest_frame(self) -> Optional[np.ndarray]:
        if self.active_frame is not None:
            return self.active_frame.copy()
        if self.camera:
            try:
                frame = self.camera.get_frame()
                if frame is not None:
                    self.active_frame = frame
                    return frame.copy()
            except Exception:
                pass
        return None

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
                if idx == current_usb_idx:
                    act_w = getattr(self.camera, "actual_width", self.width) if self.camera else self.width
                    act_h = getattr(self.camera, "actual_height", self.height) if self.camera else self.height
                    is_open = getattr(self.camera, "is_opened", False) if self.camera else False
                    devices.append({
                        "index": idx,
                        "name": f"USB Camera {idx}" + (" (Active)" if is_open else " (Selected)"),
                        "resolution": f"{act_w}x{act_h}",
                        "available": is_open,
                        "is_current": True
                    })
                    continue

                cap = None
                try:
                    cap = cv2.VideoCapture(idx, backend)
                    if not cap.isOpened() and platform.system() != "Windows":
                        cap = cv2.VideoCapture(idx)

                    if cap and cap.isOpened():
                        devices.append({
                            "index": idx,
                            "name": f"USB Camera {idx}",
                            "resolution": "1280x720",
                            "available": True,
                            "is_current": (idx == current_usb_idx)
                        })
                except Exception as e:
                    print(f"[CameraService] Probe error index {idx}: {e}")
                finally:
                    if cap is not None:
                        try:
                            cap.release()
                        except Exception:
                            pass

            if not devices:
                devices.append({
                    "index": 0,
                    "name": "USB Camera 0 (Not Detected)",
                    "resolution": "1280x720",
                    "available": False,
                    "is_current": (self.device_index == 0)
                })

            self._cached_devices = devices
            self._last_probe_time = now
            return devices

camera_service = CameraService()
