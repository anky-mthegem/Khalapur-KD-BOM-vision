"""
Application Configuration for Industrial Conveyor Belt BOM Vision Inspector.
Adheres strictly to the cross-platform mandate using pathlib.Path.
"""
from pathlib import Path
from pydantic import BaseModel
import os

# Root directories
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
DATASETS_DIR = BASE_DIR / "datasets" / "bom_dataset"
WEIGHTS_DIR = BASE_DIR / "models" / "weights"
STATIC_AUDIT_DIR = BASE_DIR / "static_audit"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

# Ensure all critical directories exist
for path in [DATA_DIR, DATASETS_DIR / "images" / "train", DATASETS_DIR / "images" / "val",
             DATASETS_DIR / "labels" / "train", DATASETS_DIR / "labels" / "val",
             WEIGHTS_DIR, STATIC_AUDIT_DIR, SAMPLE_DATA_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Database URLs
SQLITE_DB_PATH = DATA_DIR / "bom_vision.db"
DATABASE_URL = f"sqlite+aiosqlite:///{SQLITE_DB_PATH.as_posix()}"
SYNC_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH.as_posix()}"

# Hardware / Inspection Defaults
DEFAULT_MOCK_VIDEO = SAMPLE_DATA_DIR / "conveyor_sample.mp4"
DEFAULT_MODEL_NAME = "yolo26s-obb.pt"
DEFAULT_MODEL_WEIGHTS = WEIGHTS_DIR / DEFAULT_MODEL_NAME

# Tripwire defaults (Normalized coordinates [x1, y1, x2, y2] from 0.0 to 1.0)
DEFAULT_TRIPWIRE_COORDS = [0.55, 0.05, 0.55, 0.95]  # Vertical line at 55% width
DEFAULT_TRIPWIRE_DIRECTION = "LEFT_TO_RIGHT"  # Normal vector towards right

# Packaging keywords for automatic vision exclusion
PACKAGING_KEYWORDS = [
    "CARTON",
    "CORRUGATED BOX",
    "MASTER BAG",
    "POLYBAG",
    "PACKING BOX",
    "CORRUGATED SHEET",
    "BUBBLE WRAP",
    "PACKING TAPE",
    "LABEL",
    "BOX (",
    "CARTON ("
]

class SystemSettings(BaseModel):
    app_name: str = "KD-BOM Vision Inspector"
    version: str = "2.6.0-OBB"
    plant_line: str = "Plant Line 1 (Khalapur)"
    active_master_code: str = "31162814SD05076"
    active_model_name: str = DEFAULT_MODEL_NAME
    camera_mode: str = "MOCK"  # "MOCK", "USB", "RTSP"
    camera_index: int = 0
    rtsp_url: str = ""
    target_fps: int = 30
    imgsz: int = 1280
    conf_threshold: float = 0.35
    nms_mode: bool = False  # Native end-to-end inference

settings = SystemSettings()
