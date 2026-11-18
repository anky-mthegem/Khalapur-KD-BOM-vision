"""
Virtual Tripwire Crossing Detection & 100% Match QC Gate Engine.
"""
import math
import uuid
import threading
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from backend.app.config import DEFAULT_TRIPWIRE_COORDS, DEFAULT_TRIPWIRE_DIRECTION, STATIC_AUDIT_DIR
from backend.app.database import SyncSessionLocal
from backend.app.models.recipe import BomRecipe, BomRecipeItem
from backend.app.models.session import InspectionSession, InspectionSessionCount

def ccw(A: Tuple[float, float], B: Tuple[float, float], C: Tuple[float, float]) -> bool:
    """Returns True if points A, B, C are in counter-clockwise order."""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def segments_intersect(A: Tuple[float, float], B: Tuple[float, float],
                       C: Tuple[float, float], D: Tuple[float, float]) -> bool:
    """Returns True if line segments AB and CD intersect."""
    return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))

class TripwireService:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TripwireService, cls).__new__(cls)
                cls._instance.coords = list(DEFAULT_TRIPWIRE_COORDS)
                cls._instance.direction = DEFAULT_TRIPWIRE_DIRECTION
                cls._instance.active_session_uid: Optional[str] = None
                cls._instance.active_recipe_code: Optional[str] = None
                cls._instance.active_recipe_desc: Optional[str] = None
                cls._instance.recipe_items: List[Dict[str, Any]] = []
                cls._instance.counts: Dict[str, int] = {}
                cls._instance.crossed_track_ids: Set[int] = set()
                cls._instance.event_listeners: List[Any] = []
            return cls._instance

    def set_tripwire(self, coords: List[float], direction: str = "LEFT_TO_RIGHT"):
        with self._lock:
            self.coords = coords
            self.direction = direction

    def get_tripwire(self) -> Dict[str, Any]:
        return {
            "coords": self.coords,
            "direction": self.direction
        }

    def start_session(self, master_item_code: str, operator_notes: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            session_uid = str(uuid.uuid4())
            self.active_session_uid = session_uid
            self.active_recipe_code = master_item_code
            self.crossed_track_ids.clear()
            self.counts.clear()

            with SyncSessionLocal() as db:
                recipe = db.query(BomRecipe).filter_by(master_item_code=master_item_code).first()
                if not recipe:
                    raise ValueError(f"Recipe {master_item_code} not found in database.")

                self.active_recipe_desc = recipe.description
                self.recipe_items = [it.to_dict() for it in recipe.items]
                for it in self.recipe_items:
                    self.counts[it["part_uid"]] = 0

                total_target = sum(it["target_qty"] for it in self.recipe_items if it["is_vision_inspected"])

                new_session = InspectionSession(
                    session_uid=session_uid,
                    recipe_id=recipe.id,
                    master_item_code=master_item_code,
                    start_time=datetime.utcnow(),
                    status="IN_PROGRESS",
                    total_target=total_target,
                    total_counted=0,
                    operator_notes=operator_notes
                )
                db.add(new_session)
                db.flush()

                for it in self.recipe_items:
                    count_rec = InspectionSessionCount(
                        session_id=new_session.id,
                        part_uid=it["part_uid"],
                        target_qty=it["target_qty"],
                        counted_qty=0,
                        status="PENDING"
                    )
                    db.add(count_rec)
                db.commit()

            return self.get_current_state()

    def reset_counts(self):
        with self._lock:
            self.crossed_track_ids.clear()
            for k in self.counts:
                self.counts[k] = 0

            if self.active_session_uid:
                with SyncSessionLocal() as db:
                    session = db.query(InspectionSession).filter_by(session_uid=self.active_session_uid).first()
                    if session:
                        session.total_counted = 0
                        for c in session.counts:
                            c.counted_qty = 0
                            c.status = "PENDING"
                        db.commit()

    def check_tripwire_crossings(self, tracked_objects: List[Dict[str, Any]], frame_w: int, frame_h: int) -> List[Dict[str, Any]]:
        """
        Calculates geometric intersections between object trajectory and the tripwire line segment.
        """
        cross_events: List[Dict[str, Any]] = []
        if not self.active_session_uid:
            return cross_events

        # Absolute tripwire line points
        P1 = (self.coords[0] * frame_w, self.coords[1] * frame_h)
        P2 = (self.coords[2] * frame_w, self.coords[3] * frame_h)

        # Ensure P1 is top/left of P2 for consistent normal vector
        if P1[1] > P2[1] or (P1[1] == P2[1] and P1[0] > P2[0]):
            P1, P2 = P2, P1

        dx = P2[0] - P1[0]
        dy = P2[1] - P1[1]

        # Normal vector pointing to the right (+x) / downwards (+y)
        normal = (dy, -dx)

        with self._lock:
            for obj in tracked_objects:
                tid = obj["track_id"]
                if tid in self.crossed_track_ids:
                    continue

                prev_c = obj.get("prev_centroid")
                curr_c = obj.get("centroid")
                if not prev_c or not curr_c:
                    continue

                # Check if movement segment intersects tripwire line
                if segments_intersect(prev_c, curr_c, P1, P2):
                    # Check directional flow
                    vx = curr_c[0] - prev_c[0]
                    vy = curr_c[1] - prev_c[1]
                    dot = vx * normal[0] + vy * normal[1]

                    # Left-to-right default: normal vector points right
                    if self.direction == "LEFT_TO_RIGHT" and dot < 0:
                        continue
                    elif self.direction == "RIGHT_TO_LEFT" and dot > 0:
                        continue

                    # Register crossing!
                    self.crossed_track_ids.add(tid)
                    part_uid = obj["part_uid"]

                    if part_uid in self.counts:
                        self.counts[part_uid] += 1
                    else:
                        self.counts[part_uid] = 1

                    event_data = {
                        "track_id": tid,
                        "part_uid": part_uid,
                        "item_name": obj["item_name"],
                        "new_count": self.counts[part_uid],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    cross_events.append(event_data)

                    # Update database asynchronously
                    self._update_db_count(part_uid, self.counts[part_uid])

        return cross_events

    def _update_db_count(self, part_uid: str, new_count: int):
        try:
            with SyncSessionLocal() as db:
                session = db.query(InspectionSession).filter_by(session_uid=self.active_session_uid).first()
                if session:
                    session.total_counted = sum(
                        self.counts.get(it["part_uid"], 0)
                        for it in self.recipe_items
                        if it["is_vision_inspected"]
                    )
                    count_rec = db.query(InspectionSessionCount).filter_by(
                        session_id=session.id, part_uid=part_uid
                    ).first()
                    if count_rec:
                        count_rec.counted_qty = new_count
                        count_rec.last_counted_at = datetime.utcnow()
                        if new_count == count_rec.target_qty:
                            count_rec.status = "MATCH"
                        elif new_count > count_rec.target_qty:
                            count_rec.status = "OVERCOUNT"
                        else:
                            count_rec.status = "IN_PROGRESS"
                    db.commit()
        except Exception as e:
            print(f"[TripwireService] Error updating session count: {e}")

    def simulate_crossing(self, part_uid: str, item_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Manually injects an item crossing event for testing/simulation.
        Increments item counter and updates database session record.
        """
        with self._lock:
            if not self.active_session_uid:
                raise ValueError("No active inspection session is running.")
            if part_uid in self.counts:
                self.counts[part_uid] += 1
            else:
                self.counts[part_uid] = 1
            new_count = self.counts[part_uid]
            self._update_db_count(part_uid, new_count)
            return {
                "part_uid": part_uid,
                "item_name": item_name or part_uid,
                "new_count": new_count,
                "state": self.get_current_state()
            }

    def sync_item_vision_inspection(self, item_id: int, is_vision_inspected: bool):
        """
        Syncs in-memory recipe item vision inspection flag when toggled by operator in UI.
        """
        with self._lock:
            for it in self.recipe_items:
                if it.get("id") == item_id:
                    it["is_vision_inspected"] = is_vision_inspected
                    break

    def render_tripwire_overlay(self, frame: np.ndarray) -> np.ndarray:
        vis = frame.copy()
        h, w = vis.shape[:2]
        p1 = (int(self.coords[0] * w), int(self.coords[1] * h))
        p2 = (int(self.coords[2] * w), int(self.coords[3] * h))

        # Cyan tripwire line
        cv2.line(vis, p1, p2, (255, 255, 0), 3)
        # End handles
        cv2.circle(vis, p1, 7, (0, 255, 255), -1)
        cv2.circle(vis, p2, 7, (0, 255, 255), -1)
        
        # Label
        mid_x = (p1[0] + p2[0]) // 2
        mid_y = (p1[1] + p2[1]) // 2
        cv2.putText(vis, "VIRTUAL TRIPWIRE", (mid_x + 10, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        return vis

    def get_current_state(self) -> Dict[str, Any]:
        with self._lock:
            items_status = []
            total_target = 0
            total_counted = 0
            all_match = True

            for it in self.recipe_items:
                p_uid = it["part_uid"]
                target = it["target_qty"]
                counted = self.counts.get(p_uid, 0)
                is_vis = it["is_vision_inspected"]

                if is_vis:
                    total_target += target
                    total_counted += counted

                if not is_vis:
                    status = "EXCLUDED"
                elif counted == target:
                    status = "MATCH"
                elif counted > target:
                    status = "OVERCOUNT"
                    all_match = False
                elif counted > 0:
                    status = "IN_PROGRESS"
                    all_match = False
                else:
                    status = "PENDING"
                    all_match = False

                items_status.append({
                    "id": it.get("id"),
                    "sr_no": it["sr_no"],
                    "part_uid": p_uid,
                    "item_name": it["item_name"],
                    "drawing_no": it["drawing_no"],
                    "target_qty": target,
                    "counted_qty": counted,
                    "is_vision_inspected": is_vis,
                    "status": status
                })

            overall_status = "PASS" if (all_match and total_target > 0) else "IN_PROGRESS"

            return {
                "session_uid": self.active_session_uid,
                "master_item_code": self.active_recipe_code,
                "recipe_description": getattr(self, "active_recipe_desc", None),
                "total_target": total_target,
                "total_counted": total_counted,
                "overall_status": overall_status,
                "items": items_status
            }

    def complete_batch(self, snapshot_frame: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        100% Match QC Gate:
        Evaluates all is_vision_inspected items. If all match target, PASS.
        If any missing or over-counted, BLOCK with full error details.
        """
        state = self.get_current_state()
        missing = []
        overcounted = []

        for item in state["items"]:
            if not item["is_vision_inspected"]:
                continue
            delta = item["counted_qty"] - item["target_qty"]
            if delta < 0:
                missing.append({
                    "drawing_no": item["drawing_no"],
                    "item_name": item["item_name"],
                    "target_qty": item["target_qty"],
                    "counted_qty": item["counted_qty"],
                    "missing_qty": abs(delta)
                })
            elif delta > 0:
                overcounted.append({
                    "drawing_no": item["drawing_no"],
                    "item_name": item["item_name"],
                    "target_qty": item["target_qty"],
                    "counted_qty": item["counted_qty"],
                    "over_qty": delta
                })

        snapshot_url = None
        if snapshot_frame is not None and self.active_session_uid:
            snap_filename = f"batch_{self.active_session_uid[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
            snap_path = STATIC_AUDIT_DIR / snap_filename
            cv2.imwrite(str(snap_path), snapshot_frame)
            snapshot_url = f"/api/audit/snapshots/{snap_filename}"

        is_passed = (len(missing) == 0 and len(overcounted) == 0 and state["total_target"] > 0)
        final_status = "PASSED" if is_passed else "BLOCKED"

        # Update DB session record
        if self.active_session_uid:
            with SyncSessionLocal() as db:
                session = db.query(InspectionSession).filter_by(session_uid=self.active_session_uid).first()
                if session:
                    session.end_time = datetime.utcnow()
                    session.status = final_status
                    session.snapshot_path = snapshot_url
                    db.commit()

        qc_token = f"QC-{uuid.uuid4().hex[:8].upper()}" if is_passed else None

        return {
            "status": final_status,
            "session_uid": self.active_session_uid or "",
            "total_target": state["total_target"],
            "total_counted": state["total_counted"],
            "missing_items": missing,
            "overcounted_items": overcounted,
            "snapshot_url": snapshot_url,
            "qc_token": qc_token,
            "message": "Batch verified 100% PASS. Ready for QC Label Print." if is_passed else "Batch BLOCKED! Hardware kit incomplete or over-counted."
        }

tripwire_service = TripwireService()
