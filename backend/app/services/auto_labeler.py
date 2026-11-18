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

        # Lookup class IDs from DB by drawing_no, part_uid, or item_name
        with SyncSessionLocal() as db:
            parts = db.query(PartsCatalog).all()
            dwg_map = {p.drawing_no.strip().upper(): p.yolo_class_id for p in parts if p.drawing_no}
            part_map = {p.part_uid.strip().upper(): p.yolo_class_id for p in parts if p.part_uid}
            name_map = {p.item_name: p.yolo_class_id for p in parts if p.item_name}

            lines = []
            labeled_parts_set = set()
            for ann in annotations:
                dwg_no = (ann.get("drawing_no") or "").strip().upper()
                part_uid = (ann.get("part_uid") or "").strip().upper()
                item_name = ann.get("item_name") or ann.get("label")
                
                class_id = None
                matched_key = None
                if dwg_no and dwg_no in dwg_map:
                    class_id = dwg_map[dwg_no]
                    matched_key = dwg_no
                elif part_uid and part_uid in part_map:
                    class_id = part_map[part_uid]
                    matched_key = part_uid
                elif item_name and item_name in name_map:
                    class_id = name_map[item_name]
                    matched_key = item_name
                
                if class_id is None:
                    continue

                poly = ann.get("polygon")
                if not poly or len(poly) < 4:
                    poly = [[0.05, 0.05], [0.95, 0.05], [0.95, 0.95], [0.05, 0.95]]
                
                coords_flat = [f"{pt[0]:.6f} {pt[1]:.6f}" for pt in poly[:4]]
                line = f"{class_id} " + " ".join(coords_flat)
                lines.append(line)
                labeled_parts_set.add(matched_key)

            # Write label txt
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            # Update sample counts in database
            for p_key in labeled_parts_set:
                part = db.query(PartsCatalog).filter(
                    (PartsCatalog.drawing_no == p_key) | (PartsCatalog.part_uid == p_key) | (PartsCatalog.item_name == p_key)
                ).first()
                if part:
                    part.sample_count += 1
                    if part.sample_count >= 1 and part.training_status == "UNTRAINED":
                        part.training_status = "LABELED"
            
            # Record labeled frame
            frame_rec = LabeledFrame(
                image_path=f"datasets/bom_dataset/images/train/{img_filename}",
                label_path=f"datasets/bom_dataset/labels/train/{txt_filename}",
                source="CAMERA_CAPTURE" if not annotations or not annotations[0].get("is_browse_upload") else "BROWSE_UPLOAD",
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
            "file_id": file_id,
            "filename": img_filename
        }

    @staticmethod
    def get_dataset_summary() -> Dict[str, Any]:
        """
        Returns the list and count of all images in the training folder,
        along with sample counts per item_name.
        """
        train_img_dir = DATASETS_DIR / "images" / "train"
        train_lbl_dir = DATASETS_DIR / "labels" / "train"
        train_img_dir.mkdir(parents=True, exist_ok=True)
        train_lbl_dir.mkdir(parents=True, exist_ok=True)

        img_files = sorted(
            list(train_img_dir.glob("*.jpg")) + list(train_img_dir.glob("*.png")),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        with SyncSessionLocal() as db:
            parts = db.query(PartsCatalog).order_by(PartsCatalog.yolo_class_id).all()
            id_to_name = {p.yolo_class_id: p.item_name for p in parts}
            part_counts = {p.item_name: 0 for p in parts}

            samples = []
            for img in img_files[:50]:  # latest 50
                lbl_path = train_lbl_dir / f"{img.stem}.txt"
                assigned_names = []
                if lbl_path.exists():
                    with open(lbl_path, "r", encoding="utf-8") as f:
                        for line in f:
                            parts_tokens = line.strip().split()
                            if parts_tokens:
                                try:
                                    cid = int(parts_tokens[0])
                                    cname = id_to_name.get(cid, f"Class {cid}")
                                    assigned_names.append(cname)
                                    if cname in part_counts:
                                        part_counts[cname] += 1
                                except ValueError:
                                    pass

                samples.append({
                    "filename": img.name,
                    "stem": img.stem,
                    "labels": assigned_names if assigned_names else ["Unassigned"],
                    "primary_label": assigned_names[0] if assigned_names else "Unassigned",
                    "timestamp": datetime.fromtimestamp(img.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })

            # Calculate total overall counts
            for p in parts:
                if p.item_name in part_counts:
                    p.sample_count = max(p.sample_count, part_counts[p.item_name])

            parts_summary = [
                {
                    "item_name": p.item_name,
                    "drawing_no": p.drawing_no or "—",
                    "yolo_class_id": p.yolo_class_id,
                    "sample_count": part_counts.get(p.item_name, p.sample_count),
                    "training_status": p.training_status
                }
                for p in parts
            ]
            db.commit()

        return {
            "total_images": len(img_files),
            "samples": samples,
            "parts_summary": parts_summary
        }

auto_labeler = AutoLabelerService()
