"""
Parts Catalog ORM Model.
Tracks the global parts registry, persistent contiguous YOLO class IDs, and training statuses.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from backend.app.database import Base

class PartsCatalog(Base):
    __tablename__ = "parts_catalog"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    part_uid = Column(String(128), unique=True, index=True, nullable=False)
    item_name = Column(String(255), nullable=False)
    drawing_no = Column(String(64), nullable=True)
    yolo_class_id = Column(Integer, unique=True, index=True, nullable=False)
    training_status = Column(String(32), default="UNTRAINED", nullable=False)  # UNTRAINED, LABELED, TRAINED
    sample_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "part_uid": self.part_uid,
            "item_name": self.item_name,
            "drawing_no": self.drawing_no or "—",
            "yolo_class_id": self.yolo_class_id,
            "training_status": self.training_status,
            "sample_count": self.sample_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
