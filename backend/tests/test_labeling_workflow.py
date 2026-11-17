"""
Unit tests for Component Image Browsing, Labeling with Item Names, and YOLO Training Workflow.
"""
import cv2
import numpy as np
import base64
import pytest
from backend.app.services.auto_labeler import auto_labeler
from backend.app.services.training_service import training_service
from backend.app.database import SyncSessionLocal
from backend.app.services.seed_data import seed_database_sync

def test_save_component_image_and_summary():
    with SyncSessionLocal() as db:
        seed_database_sync(db)

    # Create dummy component image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.circle(img, (320, 240), 50, (200, 200, 200), -1)

    # Save component with item_name as label
    item_label = "LEVELER FOR LEG KREATION X3"
    res = auto_labeler.save_labeled_frame(
        image=img,
        annotations=[{
            "item_name": item_label,
            "part_uid": "HOM196273",
            "polygon": [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]],
            "is_browse_upload": True
        }],
        master_item_code="31162814SD05076"
    )

    assert res["boxes_saved"] == 1
    assert "frame_" in res["file_id"]

    # Verify summary
    summary = auto_labeler.get_dataset_summary()
    assert summary["total_images"] >= 1
    matched_part = next((p for p in summary["parts_summary"] if p["item_name"] == item_label), None)
    assert matched_part is not None
    assert matched_part["sample_count"] >= 1

def test_data_yaml_uses_item_names():
    yaml_path = training_service.generate_data_yaml()
    assert yaml_path.exists()
    import yaml
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    assert "names" in config
    # Ensure values in names are item_names
    names_vals = list(config["names"].values())
    assert any("LEVELER" in str(v) or "SCREW" in str(v) for v in names_vals)
