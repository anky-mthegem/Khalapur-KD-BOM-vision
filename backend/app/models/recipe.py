"""
BOM Recipe & Line Items ORM Models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class BomRecipe(Base):
    __tablename__ = "bom_recipes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    master_item_code = Column(String(64), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=False)
    total_items = Column(Integer, default=0, nullable=False)
    vision_items_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    items = relationship("BomRecipeItem", back_populates="recipe", cascade="all, delete-orphan", order_by="BomRecipeItem.sr_no", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "master_item_code": self.master_item_code,
            "description": self.description,
            "total_items": self.total_items,
            "vision_items_count": self.vision_items_count,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class BomRecipeItem(Base):
    __tablename__ = "bom_recipe_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("bom_recipes.id", ondelete="CASCADE"), nullable=False)
    sr_no = Column(Integer, nullable=False)
    part_uid = Column(String(128), ForeignKey("parts_catalog.part_uid"), nullable=False)
    item_name = Column(String(255), nullable=False)
    drawing_no = Column(String(64), nullable=True)
    target_qty = Column(Integer, nullable=False)
    is_vision_inspected = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    recipe = relationship("BomRecipe", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "sr_no": self.sr_no,
            "part_uid": self.part_uid,
            "item_name": self.item_name,
            "drawing_no": self.drawing_no or "—",
            "target_qty": self.target_qty,
            "is_vision_inspected": self.is_vision_inspected,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
