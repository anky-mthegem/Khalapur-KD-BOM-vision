"""
Unit tests for YOLO-OBB dataset export & data.yaml generation.
"""
import yaml
import pytest
from backend.app.services.training_service import training_service
from backend.app.config import DATASETS_DIR

def test_data_yaml_generation():
    from backend.app.database import SyncSessionLocal
    from backend.app.services.seed_data import seed_database_sync

    with SyncSessionLocal() as db:
        seed_database_sync(db)

    yaml_path = training_service.generate_data_yaml()
    assert yaml_path.exists()

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "names" in data
    assert "train" in data
    assert "val" in data
    assert 0 in data["names"]
    assert isinstance(data["names"][0], str)
