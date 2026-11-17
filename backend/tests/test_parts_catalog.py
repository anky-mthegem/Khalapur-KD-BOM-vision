"""
Unit tests for Parts Catalog contiguous class IDs and upsert logic.
"""
import pytest
from backend.app.database import SyncSessionLocal
from backend.app.models.parts import PartsCatalog
from backend.app.services.seed_data import seed_database_sync

def test_parts_catalog_contiguous_class_ids():
    with SyncSessionLocal() as db:
        seed_database_sync(db)
        parts = db.query(PartsCatalog).order_by(PartsCatalog.yolo_class_id).all()
        assert len(parts) >= 16

        # Check contiguous IDs 0, 1, 2, ...
        class_ids = [p.yolo_class_id for p in parts]
        expected_ids = list(range(len(parts)))
        assert class_ids == expected_ids

        # Check slug part exists
        slug_part = db.query(PartsCatalog).filter_by(
            part_uid="NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S"
        ).first()
        assert slug_part is not None
        assert slug_part.item_name == "M4 SLEEVE CONNECTING SCREW MAKE EBCO - CNS35-S"
