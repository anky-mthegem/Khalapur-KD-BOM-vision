"""
Recipe-Linked Auto-Labeling Service.
Extracts candidate Oriented Bounding Boxes (OBB) using OpenCV contour analysis,
and persists verified polygon annotations into YOLO-OBB format.
"""
import cv2
import uuid
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from backend.app.config import DATASETS_DIR
from backend.app.database import SyncSessionLocal
from backend.app.models.parts import PartsCatalog
from backend.app.models.dataset import LabeledFrame

class AutoLabelerService:
    @staticmethod
    def auto_segment_contours(
        image: np.ndarray,
        threshold_val: int = 60,
        blur_kernel: int = 5,
        min_area: int = 300,
        max_area: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Runs OpenCV adaptive contour segmentation and generates oriented bounding boxes (OBB).
        Returns list of boxes with 4-corner polygon coordinates and center.
        """
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        k = max(3, blur_kernel if blur_kernel % 2 != 0 else blur_kernel + 1)
        blur = cv2.GaussianBlur(gray, (k, k), 0)
        
        _, thresh = cv2.threshold(blur, threshold_val, 255, cv2.THRESH_BINARY)
        # Morphological close to bridge fastener screw threads
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        proposals: List[Dict[str, Any]] = []
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if min_area <= area <= max_area:
                rect = cv2.minAreaRect(cnt)  # ((cx, cy), (w, h), angle)
                box = cv2.boxPoints(rect)     # (4, 2)
                
                # Normalize coordinates (0.0 to 1.0)
                norm_polygon = [[float(pt[0] / w), float(pt[1] / h)] for pt in box]
                
                proposals.append({
                    "id": f"prop_{i}_{uuid.uuid4().hex[:4]}",
                    "polygon": norm_polygon,
                    "center": [float(rect[0][0] / w), float(rect[0][1] / h)],
                    "width": float(rect[1][0] / w),
                    "height": float(rect[1][1] / h),
                    "angle": float(rect[2]),
                    "area": float(area),
                    "part_uid": ""
                })

        return proposals

    @staticmethod
    def save_labeled_frame(
        image: np.ndarray,
        annotations: List[Dict[str, Any]],
        master_item_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Saves image and normalized YOLO-OBB format label file.
        Format per line: class_id x1 y1 x2 y2 x3 y4
        """
        file_id = f"frame_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        img_filename = f"{file_id}.jpg"
        txt_filename = f"{file_id}.txt"

        img_path = DATASETS_DIR / "images" / "train" / img_filename
        txt_path = DATASETS_DIR / "labels" / "train" / txt_filename

        cv2.imwrite(str(img_path), image)

        # Lookup class IDs from DB
        with SyncSessionLocal() as db:
            parts = db.query(PartsCatalog).all()
            part_map = {p.part_uid: p.yolo_class_id for p in parts}

            lines = []
            labeled_parts_set = set()
            for ann in annotations:
                part_uid = ann.get("part_uid")
                if not part_uid or part_uid not in part_map:
                    continue
                class_id = part_map[part_uid]
                poly = ann["polygon"]  # 4 points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                coords_flat = [f"{pt[0]:.6f} {pt[1]:.6f}" for pt in poly]
                line = f"{class_id} " + " ".join(coords_flat)
                lines.append(line)
                labeled_parts_set.add(part_uid)

            # Write label txt
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            # Update sample counts in database
            for p_uid in labeled_parts_set:
                part = db.query(PartsCatalog).filter_by(part_uid=p_uid).first()
                if part:
                    part.sample_count += 1
                    if part.sample_count >= 10 and part.training_status == "UNTRAINED":
                        part.training_status = "LABELED"
            
            # Record labeled frame
            frame_rec = LabeledFrame(
                image_path=f"datasets/bom_dataset/images/train/{img_filename}",
                label_path=f"datasets/bom_dataset/labels/train/{txt_filename}",
                source="CAMERA_CAPTURE",
                master_item_code=master_item_code,
                annotated_boxes_count=len(lines),
                is_verified=True
            )
            db.add(frame_rec)
            db.commit()

        return {
            "image_path": str(img_path),
            "label_path": str(txt_path),
            "boxes_saved": len(lines),
            "file_id": file_id
        }

auto_labeler = AutoLabelerService()
