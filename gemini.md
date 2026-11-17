# Project Rules: Industrial BOM Vision Inspector

## Cross-Platform Mandate (Windows 11 Dev -> Ubuntu Linux Prod)
- Use `pathlib.Path` for ALL file, dataset, and model paths. Never hardcode `\` or `/` or drive letters (`C:\`).
- Use SQLite (`aiosqlite` / `SQLAlchemy`) for local persistence so the app runs zero-config on both Windows 11 and Ubuntu.
- Abstract hardware interfaces (Camera, PLC/Relay, Barcode Scanner) behind clean Python interfaces with a `MockHardware` mode (video file / test folder playback + simulated barcode input) so full end-to-end testing works on Windows 11 without physical conveyor hardware.
- Keep `requirements.txt` cross-platform compatible (avoid `pywin32` or Linux-only packages without `sys_platform` markers).

## UI Design System: "Industrial Office Ribbon"
- Target users: Manufacturing plant operators & quality engineers familiar with Microsoft Word / Excel.
- Aesthetic: High-contrast, utilitarian, light-mode "MS Office Ribbon" layout—NO dark-mode SaaS gradients, floating glassmorphism, or hidden hamburger menus.
- Layout Structure:
  1. **Top Title Bar**: App title, active Master Item Code badge, hardware status pills (Camera, Model, PLC), and Window/Session status.
  2. **MS Word-Style Ribbon Toolbar**: Categorized tabs (`Home / Inspection`, `BOM Recipes`, `Dataset & Labeling`, `Model Training`, `Audit Logs`) with large, clearly labeled icon+text buttons grouped by vertical dividers.
  3. **Main Workspace Split**:
     - Left/Center (65%): High-contrast live conveyor viewport with virtual tripwire overlay, oriented bounding boxes (OBB), and large status banner (`PASS` in `#107C10` green / `MISSING ITEMS` in `#D13438` red).
     - Right Pane (35%): Excel-style dense BOM Recipe Grid (`Sr No`, `Item Name`, `Drawing No`, `Target Qty`, `Counted`, `Status`) with color-coded row highlights.
  4. **Bottom Status Bar** (MS Word blue `#2B579A` or slate): Live FPS, active YOLO26 model filename, total batch pass/fail counter, and zoom/camera controls.

## Verification Loop
- After implementing any module, write and run `pytest` unit tests and launch the app to verify zero startup errors and clean API responses.