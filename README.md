# Industrial Conveyor Belt BOM Vision Inspector

[![Version](https://img.shields.io/badge/version-2.6.0--OBB-blue.svg)](https://github.com)
[![Platform](https://img.shields.io/badge/platform-Windows%2011%20%7C%20Ubuntu%20LTS-success.svg)](https://github.com)
[![Inference](https://img.shields.io/badge/YOLO26-OBB%20(nms=False)-orange.svg)](https://github.com)
[![UI](https://img.shields.io/badge/UI-Office%20Ribbon-107C41.svg)](https://github.com)

A self-contained, offline-capable computer vision system built for manufacturing packaging verification (Khalapur KD plant). The system imports manufacturing plant Excel BOM spreadsheets, registers items in a global persistent parts catalog, and verifies hardware kits crossing a virtual tripwire on a conveyor belt using YOLO26-OBB (`nms=False` native end-to-end inference) and ByteTrack object tracking.

---

## Key Features

1. **Plant Excel BOM Importer & Canonical Part Registry**:
   - `openpyxl` parser designed specifically for manufacturing BOM layouts.
   - Extracts `Item Code(Master)` (e.g. `31162814SD05076`) and `Description` across merged and unmerged header cells.
   - **Canonical `part_uid` Slugging**: Converts valid drawing numbers (e.g. `HOM196273`) into clean uppercase keys. Automatically converts missing, dash (`—`), or blank drawing numbers into deterministic slugs (e.g. `NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S`).
   - **Packaging Auto-Exclusion**: Automatically identifies packaging keywords (`CARTON`, `CORRUGATED BOX`, `MASTER BAG`, `POLYBAG`) and sets `is_vision_inspected = False`, excluding them from tripwire verification while keeping them visible in the BOM table.
   - **Global Parts Catalog**: Maintains persistent, contiguous 0-indexed integer `yolo_class_id` keys (`0..N-1`) and tracks status (`UNTRAINED`, `LABELED`, `TRAINED`).
   - Pre-seeded with the plant's 16-item hardware kit `31162814SD05076`.

2. **Live Conveyor Inspection & Virtual Tripwire Counting**:
   - High-contrast 65% conveyor viewport with real-time video stream and 35% Excel-dense spreadsheet grid.
   - Configurable **Virtual Tripwire**: 2D vector normal line crossing math with directional flow checking and unique `track_id` debouncing.
   - **100% Match QC Gate**: Verifies all vision-inspected items match the exact target BOM quantity. Blocks incomplete batches with a high-contrast Red Alert modal listing exact missing parts, and produces audit snapshots with verification tokens on pass.
   - **Windows 11 Offline Dev Mode**: Built-in synthetic conveyor generator with moving hardware fasteners and test crossing simulation.

3. **Recipe-Linked Auto-Labeling Studio**:
   - One-click OpenCV adaptive contour segmentation to auto-propose Oriented Bounding Boxes (OBB).
   - Interactive HTML5 Canvas editor to translate, scale, and rotate boxes.
   - Direct export to normalized YOLO-OBB dataset format (`datasets/bom_dataset/images` & `labels`).

4. **Built-In YOLO26 Training Pipeline**:
   - Dynamically generates `data.yaml` mapped to the SQLite `parts_catalog`.
   - Background Ultralytics training runner (`yolo26n-obb.pt`, `yolo26s-obb.pt`, `yolo26m-obb.pt`) with real-time loss and mAP streaming.
   - **"Activate Model"** live hot-swapping without server restart.

5. **"Industrial Office Ribbon" UI**:
   - Strictly designed for manufacturing operators familiar with Microsoft Word & Excel.
   - Utilitarian light-mode ribbon toolbar, dense tabular typography, color-coded rows (`MATCH`, `IN_PROGRESS`, `OVERCOUNT`, `EXCLUDED`), and MS Word Blue (`#2B579A`) status bar.

---

## One-Click Windows 11 Dev & Testing (Zero Manual Intervention)

Double-click or run:
```cmd
start_windows.bat
```
This batch script automatically:
1. Detects Python 3.10/3.11.
2. Creates the dedicated `.venv` virtual environment.
3. Verifies and installs all backend dependencies.
4. Verifies the pre-bundled production frontend.
5. Launches the inspection station server on `http://localhost:8000`.
6. Automatically opens your default web browser to the application.

---

## Ubuntu 22.04 / 24.04 LTS Production Deployment

Run the automated provisioning script:
```bash
chmod +x deployment/setup_ubuntu.sh
./deployment/setup_ubuntu.sh
```

To manage the background `systemd` service:
```bash
sudo systemctl status bom-inspector.service
sudo systemctl restart bom-inspector.service
sudo journalctl -u bom-inspector.service -f
```

---

## Verification & Unit Testing

Run the automated `pytest` test suite:
```cmd
.\.venv\Scripts\python.exe -m pytest backend/tests
```

All 9 unit tests verify:
- Plant Excel BOM parser merged headers, canonical slugging, and packaging exclusion.
- 2D mathematical tripwire intersection, directional normal gating, and track ID debouncing.
- 100% Match QC Gate PASS vs BLOCKED states.
- Contiguous YOLO class ID assignment in `parts_catalog`.
- YOLO-OBB `data.yaml` export.

---

## Project Structure

```
khalapur-kd-bom-vision/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint & lifespan
│   │   ├── config.py           # Cross-platform pathlib.Path configuration
│   │   ├── database.py         # SQLite SQLAlchemy engine & session maker
│   │   ├── models/             # ORM models (Parts, Recipe, Session, Training)
│   │   ├── schemas/            # Pydantic validation schemas
│   │   ├── services/           # Excel parser, Camera, Vision, Tripwire, Labeler, Training
│   │   └── routes/             # REST & WebSocket API endpoints
│   ├── tests/                  # Automated pytest test suites
│   ├── datasets/               # YOLO-OBB training datasets
│   ├── sample_data/            # Sample Excel sheets and test data
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/layout/  # TitleBar, RibbonToolbar, StatusBar
│   │   ├── components/inspection/ # ConveyorViewport, BomGrid, QcAlertModal
│   │   ├── components/bom/     # ExcelUploadModal, BomRecipesTab
│   │   ├── components/labeling/# LabelingStudioTab
│   │   ├── components/training/# ModelTrainingTab
│   │   ├── components/audit/   # AuditLogsTab
│   │   ├── services/api.ts     # Frontend API client
│   │   └── App.tsx             # Main coordinator
│   └── dist/                   # Compiled production single-port assets
├── deployment/
│   ├── start_windows.bat       # Windows launcher
│   ├── setup_ubuntu.sh         # Ubuntu provisioning script
│   └── bom-inspector.service   # Systemd service unit
├── start_windows.bat           # Root zero-intervention Windows launcher
├── GEMINI.md                   # Project architectural & UI rules
└── IMPLEMENTATION_PLAN.md      # Detailed engineering specification
```

---

## Author & Engineering Credits

Made By ❤️ By Aman  
*Industrial Vision & Automation Engineering | Khalapur KD Plant*

