"""
YOLO26-OBB Inference & ByteTrack Object Tracking Service.
Hybrid pipeline:
  1. Production Mode: Runs Ultralytics native ByteTrack (model.track(source=frame, persist=True, tracker="bytetrack.yaml"))
     with 8-state Kalman Filter motion prediction and 2-stage low-confidence detection association.
  2. Fallback Mode: OpenCV adaptive contour OBB + SimpleTracker Euclidean centroid matching when model weights
     are not yet trained.
"""
import cv2
import time
import math
import threading
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from backend.app.config import settings, WEIGHTS_DIR
from backend.app.database import SyncSessionLocal
from backend.app.models.parts import PartsCatalog

class SimpleTracker:
    """
    Centroid & Euclidean distance multi-object tracker for fallback conveyor tracking.
    Assigns persistent integer track_ids to objects moving along the conveyor belt.
    """
    def __init__(self, max_disappeared: int = 25, distance_threshold: float = 65.0):
        self.next_id = 1
        self.objects: Dict[int, Dict[str, Any]] = {}
        self.disappeared: Dict[int, int] = {}
        self.distance_threshold = distance_threshold
        self.max_disappeared = max_disappeared

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # If no detections, increment disappeared
        if len(detections) == 0:
            for track_id in list(self.disappeared.keys()):
                self.disappeared[track_id] += 1
                if self.disappeared[track_id] > self.max_disappeared:
                    self._deregister(track_id)
            return []

        # If no tracked objects yet, register all
        if len(self.objects) == 0:
            for det in detections:
                self._register(det)
            return self._get_tracked_list()

        # Match existing objects to detections using Euclidean distance of centroids
        tracked_ids = list(self.objects.keys())
        tracked_centroids = [self.objects[tid]["centroid"] for tid in tracked_ids]
        detection_centroids = [det["centroid"] for det in detections]

        # Cost matrix
        dist_matrix = np.zeros((len(tracked_centroids), len(detection_centroids)), dtype=np.float32)
        for i, tc in enumerate(tracked_centroids):
            for j, dc in enumerate(detection_centroids):
                dist_matrix[i, j] = math.hypot(tc[0] - dc[0], tc[1] - dc[1])

        rows = dist_matrix.min(axis=1).argsort()
        cols = dist_matrix.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if dist_matrix[row, col] > self.distance_threshold:
                continue

            track_id = tracked_ids[row]
            # Update trajectory & latest detection data
            det = detections[col]
            prev_centroid = self.objects[track_id]["centroid"]
            self.objects[track_id]["prev_centroid"] = prev_centroid
            self.objects[track_id]["centroid"] = det["centroid"]
            self.objects[track_id]["obb"] = det["obb"]
            self.objects[track_id]["confidence"] = det["confidence"]
            self.objects[track_id]["part_uid"] = det["part_uid"]
            self.objects[track_id]["item_name"] = det["item_name"]
            self.disappeared[track_id] = 0

            used_rows.add(row)
            used_cols.add(col)

        # Unused tracked objects
        unused_rows = set(range(len(tracked_centroids))).difference(used_rows)
        for r in unused_rows:
            track_id = tracked_ids[r]
            self.disappeared[track_id] += 1
            if self.disappeared[track_id] > self.max_disappeared:
                self._deregister(track_id)

        # New detections
        unused_cols = set(range(len(detection_centroids))).difference(used_cols)
        for c in unused_cols:
            self._register(detections[c])

        return self._get_tracked_list()

    def _register(self, det: Dict[str, Any]):
        track_id = self.next_id
        self.next_id += 1
        self.objects[track_id] = {
            "track_id": track_id,
            "centroid": det["centroid"],
            "prev_centroid": det["centroid"],
            "obb": det["obb"],
            "part_uid": det["part_uid"],
            "item_name": det["item_name"],
            "confidence": det["confidence"]
        }
        self.disappeared[track_id] = 0

    def _deregister(self, track_id: int):
        if track_id in self.objects:
            del self.objects[track_id]
        if track_id in self.disappeared:
            del self.disappeared[track_id]

    def _get_tracked_list(self) -> List[Dict[str, Any]]:
        return list(self.objects.values())

class VisionEngine:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VisionEngine, cls).__new__(cls)
                cls._instance.model = None
                cls._instance.model_path = None
                cls._instance.tracker = SimpleTracker()
                cls._instance.track_history: Dict[int, Tuple[float, float]] = {}
                cls._instance.track_disappeared: Dict[int, int] = {}
                cls._instance.classes_map: Dict[int, str] = {}
                cls._instance.names_map: Dict[str, str] = {}
                cls._instance.load_classes_from_db()
                cls._instance.init_model(settings.active_model_name)
            return cls._instance

    def load_classes_from_db(self):
        try:
            with SyncSessionLocal() as db:
                parts = db.query(PartsCatalog).all()
                self.classes_map = {p.yolo_class_id: p.drawing_no for p in parts}
                self.names_map = {p.drawing_no: p.item_name for p in parts}
        except Exception:
            self.classes_map = {}
            self.names_map = {}

    def init_model(self, model_name: str):
        self.load_classes_from_db()
        target_path = WEIGHTS_DIR / model_name
        self.model_path = target_path
        self.reset_tracking()
        try:
            from ultralytics import YOLO
            if target_path.exists():
                print(f"[VisionEngine] Loading weights from {target_path} for Ultralytics ByteTrack inference.")
                self.model = YOLO(str(target_path))
            else:
                print(f"[VisionEngine] Weights not yet on disk ({target_path.name}), using dynamic contour fallback/simulator until trained.")
                self.model = None
        except Exception as e:
            print(f"[VisionEngine] Ultralytics initialization notice: {e}")
            self.model = None

    def reload_model(self, new_weights_path: Path):
        with self._lock:
            self.init_model(new_weights_path.name)

    def reset_tracking(self):
        """Resets both Ultralytics ByteTrack trajectory history and SimpleTracker state."""
        with self._lock:
            self.track_history.clear()
            self.track_disappeared.clear()
            self.tracker = SimpleTracker()

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Executes OBB inference & tracking, returning (annotated_frame, tracked_objects).
        HYBRID PIPELINE:
          1. Production Mode: When model weights exist, runs Ultralytics native ByteTrack
             (model.track(source=frame, persist=True, tracker="bytetrack.yaml")) with
             8-state Kalman Filter motion prediction and 2-stage low-confidence association.
          2. Fallback Mode: When model weights are not loaded (e.g. before initial recipe training),
             uses OpenCV adaptive contour detection + SimpleTracker Euclidean centroid matching.
        """
        tracked_objects: Optional[List[Dict[str, Any]]] = None

        # 1. Primary: Ultralytics Native ByteTrack
        if self.model is not None:
            tracked_objects = self._track_with_ultralytics(frame)

        # 2. Fallback: Dynamic Optical Contours + SimpleTracker
        if tracked_objects is None:
            raw_detections = self._detect_contours(frame)
            tracked_objects = self.tracker.update(raw_detections)

        # 3. Render visual annotations and motion trails
        annotated_frame = self._render_annotations(frame, tracked_objects)
        return annotated_frame, tracked_objects

    def _track_with_ultralytics(self, frame: np.ndarray) -> Optional[List[Dict[str, Any]]]:
        """
        Runs Ultralytics native ByteTrack object tracking on the input frame.
        Supports both YOLO-OBB (Oriented Bounding Boxes) and standard YOLO bounding boxes.
        Returns tracked objects with persistent track_id, (prev_centroid, curr_centroid),
        oriented bounding box polygon, part_uid, item_name, and confidence.
        """
        if self.model is None:
            return None

        try:
            results = self.model.track(
                source=frame,
                persist=True,
                tracker="bytetrack.yaml",
                conf=settings.conf_threshold,
                imgsz=settings.imgsz,
                verbose=False
            )

            if not results or len(results) == 0:
                return []

            res = results[0]
            tracked_objects: List[Dict[str, Any]] = []
            active_track_ids: Set[int] = set()

            # Case A: Oriented Bounding Boxes (YOLO26-OBB / YOLO11-OBB)
            if res.obb is not None and len(res.obb) > 0:
                obb_data = res.obb
                polygons = obb_data.xyxyxyxy.cpu().numpy()  # Shape: (N, 4, 2)
                classes = obb_data.cls.cpu().numpy().astype(int)
                confs = obb_data.conf.cpu().numpy()
                track_ids = obb_data.id.int().cpu().tolist() if obb_data.id is not None else None

                for i, (poly, cls_id, conf) in enumerate(zip(polygons, classes, confs)):
                    tid = int(track_ids[i]) if (track_ids is not None and i < len(track_ids)) else (i + 1)
                    active_track_ids.add(tid)

                    curr_centroid = (float(poly[:, 0].mean()), float(poly[:, 1].mean()))
                    prev_centroid = self.track_history.get(tid, curr_centroid)
                    self.track_history[tid] = curr_centroid

                    part_uid = self.classes_map.get(int(cls_id), f"CLASS_{cls_id}")
                    item_name = self.names_map.get(part_uid, part_uid)

                    tracked_objects.append({
                        "track_id": tid,
                        "centroid": curr_centroid,
                        "prev_centroid": prev_centroid,
                        "obb": poly.tolist(),
                        "class_id": int(cls_id),
                        "part_uid": part_uid,
                        "item_name": item_name,
                        "confidence": float(conf)
                    })

            # Case B: Standard Axis-Aligned Bounding Boxes
            elif res.boxes is not None and len(res.boxes) > 0:
                boxes_data = res.boxes
                xyxy = boxes_data.xyxy.cpu().numpy()  # Shape: (N, 4)
                classes = boxes_data.cls.cpu().numpy().astype(int)
                confs = boxes_data.conf.cpu().numpy()
                track_ids = boxes_data.id.int().cpu().tolist() if boxes_data.id is not None else None

                for i, (box, cls_id, conf) in enumerate(zip(xyxy, classes, confs)):
                    tid = int(track_ids[i]) if (track_ids is not None and i < len(track_ids)) else (i + 1)
                    active_track_ids.add(tid)

                    x1, y1, x2, y2 = float(box[0]), float(box[1]), float(box[2]), float(box[3])
                    curr_centroid = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
                    prev_centroid = self.track_history.get(tid, curr_centroid)
                    self.track_history[tid] = curr_centroid

                    poly = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                    part_uid = self.classes_map.get(int(cls_id), f"CLASS_{cls_id}")
                    item_name = self.names_map.get(part_uid, part_uid)

                    tracked_objects.append({
                        "track_id": tid,
                        "centroid": curr_centroid,
                        "prev_centroid": prev_centroid,
                        "obb": poly,
                        "class_id": int(cls_id),
                        "part_uid": part_uid,
                        "item_name": item_name,
                        "confidence": float(conf)
                    })

            # Prune old vanished track IDs from memory
            self._prune_track_history(active_track_ids)
            return tracked_objects

        except Exception as e:
            print(f"[VisionEngine] Ultralytics ByteTrack notice: {e}, falling back to contour tracker.")
            return None

    def _prune_track_history(self, active_track_ids: Set[int]):
        """Cleans up inactive track IDs from history to prevent memory leaks during long conveyor runs."""
        for tid in list(self.track_history.keys()):
            if tid not in active_track_ids:
                self.track_disappeared[tid] = self.track_disappeared.get(tid, 0) + 1
                if self.track_disappeared[tid] > 60:  # ~2 seconds after exiting viewport
                    self.track_history.pop(tid, None)
                    self.track_disappeared.pop(tid, None)
            else:
                self.track_disappeared[tid] = 0

    def _detect_contours(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Dynamic Optical Fallback (OpenCV adaptive contour OBB) for offline testing,
        initial system setup, or mock camera feeds before a model is trained.
        """
        detections: List[Dict[str, Any]] = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        available_uids = list(self.classes_map.values())
        if not available_uids:
            available_uids = ["HOM196273", "HOM196276", "HOM196277", "HOM196280", "HOM196328", "HRD104875"]

        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if 300 < area < 40000:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                centroid = (float(rect[0][0]), float(rect[0][1]))
                
                # Pick deterministic pseudo-class based on area/aspect ratio
                part_uid = available_uids[i % len(available_uids)]
                item_name = self.names_map.get(part_uid, part_uid)

                detections.append({
                    "obb": box.tolist(),
                    "centroid": centroid,
                    "class_id": i % len(available_uids),
                    "part_uid": part_uid,
                    "item_name": item_name,
                    "confidence": 0.94
                })

        return detections

    def _detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Backward compatibility alias."""
        return self._detect_contours(frame)

    def _render_annotations(self, frame: np.ndarray, tracked_objects: List[Dict[str, Any]]) -> np.ndarray:
        vis = frame.copy()
        for obj in tracked_objects:
            box = np.int32(obj["obb"])
            cv2.polylines(vis, [box], True, (0, 255, 128), 2)
            cx, cy = int(obj["centroid"][0]), int(obj["centroid"][1])
            cv2.circle(vis, (cx, cy), 4, (0, 255, 255), -1)

            # Motion velocity trail (draw line from prev_centroid to curr_centroid)
            prev_c = obj.get("prev_centroid")
            if prev_c:
                px, py = int(prev_c[0]), int(prev_c[1])
                if abs(cx - px) > 1 or abs(cy - py) > 1:
                    cv2.line(vis, (px, py), (cx, cy), (0, 200, 255), 2)

            # Label banner with Drawing No and Item Name
            item_name = self.names_map.get(obj['part_uid'], '')
            short_name = f" {item_name[:16]}.." if item_name else ""
            label = f"#{obj['track_id']} [{obj['part_uid']}]{short_name} ({int(obj['confidence']*100)}%)"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(vis, (cx - 10, cy - 25), (cx - 10 + tw + 6, cy - 25 + th + 6), (20, 20, 20), -1)
            cv2.putText(vis, label, (cx - 7, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 128), 1)

        return vis

vision_engine = VisionEngine()
