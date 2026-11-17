"""
Inspection Session & Real-Time Count ORM Models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class InspectionSession(Base):
    __tablename__ = "inspection_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_uid = Column(String(64), unique=True, index=True, nullable=False)
    recipe_id = Column(Integer, ForeignKey("bom_recipes.id"), nullable=False)
    master_item_code = Column(String(64), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(32), default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, PASSED, FAILED_MISSING, FAILED_OVERCOUNT, ABORTED
    total_target = Column(Integer, default=0, nullable=False)
    total_counted = Column(Integer, default=0, nullable=False)
    snapshot_path = Column(String(255), nullable=True)
    operator_notes = Column(Text, nullable=True)

    counts = relationship("InspectionSessionCount", back_populates="session", cascade="all, delete-orphan", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "session_uid": self.session_uid,
            "recipe_id": self.recipe_id,
            "master_item_code": self.master_item_code,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "total_target": self.total_target,
            "total_counted": self.total_counted,
            "snapshot_path": self.snapshot_path,
            "operator_notes": self.operator_notes,
            "counts": [c.to_dict() for c in self.counts] if self.counts else [],
        }

class InspectionSessionCount(Base):
    __tablename__ = "inspection_session_counts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("inspection_sessions.id", ondelete="CASCADE"), nullable=False)
    part_uid = Column(String(128), nullable=False)
    target_qty = Column(Integer, nullable=False)
    counted_qty = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, IN_PROGRESS, MATCH, OVERCOUNT, MISSING
    last_counted_at = Column(DateTime, nullable=True)

    session = relationship("InspectionSession", back_populates="counts")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "part_uid": self.part_uid,
            "target_qty": self.target_qty,
            "counted_qty": self.counted_qty,
            "status": self.status,
            "last_counted_at": self.last_counted_at.isoformat() if self.last_counted_at else None,
        }
