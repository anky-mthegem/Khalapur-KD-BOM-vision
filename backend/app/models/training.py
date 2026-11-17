"""
YOLO Training Runs ORM Model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.app.database import Base

class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_name = Column(String(64), nullable=False)
    base_model = Column(String(64), default="yolo26s-obb.pt", nullable=False)
    epochs = Column(Integer, default=50, nullable=False)
    imgsz = Column(Integer, default=1280, nullable=False)
    device = Column(String(32), default="auto", nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    metrics_json = Column(Text, nullable=True)
    weights_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "run_name": self.run_name,
            "base_model": self.base_model,
            "epochs": self.epochs,
            "imgsz": self.imgsz,
            "device": self.device,
            "status": self.status,
            "metrics_json": self.metrics_json,
            "weights_path": self.weights_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
