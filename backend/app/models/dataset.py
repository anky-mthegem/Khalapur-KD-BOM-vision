"""
Dataset Labeled Frames ORM Model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from backend.app.database import Base

class LabeledFrame(Base):
    __tablename__ = "labeled_frames"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_path = Column(String(255), nullable=False)
    label_path = Column(String(255), nullable=False)
    source = Column(String(32), default="CAMERA_CAPTURE", nullable=False)
    master_item_code = Column(String(64), nullable=True)
    annotated_boxes_count = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "image_path": self.image_path,
            "label_path": self.label_path,
            "source": self.source,
            "master_item_code": self.master_item_code,
            "annotated_boxes_count": self.annotated_boxes_count,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
