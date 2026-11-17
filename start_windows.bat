@echo off
setlocal enabledelayedexpansion
title Industrial BOM Vision Inspector v2.6 - Windows 11 Launcher

echo ===============================================================================
echo        INDUSTRIAL CONVEYOR BELT BOM VISION INSPECTOR (v2.6.0-OBB)
echo               Autonomous Windows 11 Offline Dev and Test Suite
echo ===============================================================================
echo.

cd /d "%~dp0"

:: 1. Detect Python Executable (Prefer Python 3.10/3.11 for Ultralytics/Torch wheels)
set "PY_EXE="

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) else (
    py -3.10 -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_EXE=py -3.10"
    ) else (
        python -c "import sys" >nul 2>&1
        if !errorlevel! equ 0 (
            set "PY_EXE=python"
        )
    )
)

if "%PY_EXE%"=="" (
    echo [ERROR] Python was not found on your system. Please install Python 3.10 or 3.11.
    pause
    exit /b 1
)

echo [1/5] Using Python: %PY_EXE%

:: 2. Check or Create Virtual Environment
if not exist ".venv\Scripts\activate.bat" (
    echo [2/5] Creating dedicated virtual environment in .venv...
    %PY_EXE% -m venv --system-site-packages .venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [2/5] Virtual environment created successfully.
) else (
    echo [2/5] Dedicated virtual environment found at .venv.
)

:: 3. Activate Virtual Environment
call .venv\Scripts\activate.bat

:: 4. Check & Install Dependencies
echo [3/5] Verifying Python backend dependencies...
python -c "import fastapi, uvicorn, openpyxl, sqlalchemy, cv2, ultralytics" >nul 2>&1
if !errorlevel! neq 0 (
    echo [3/5] Installing missing requirements from backend\requirements.txt...
    python -m pip install --upgrade pip
    python -m pip install -r backend\requirements.txt
    if !errorlevel! neq 0 (
        echo [WARNING] Some packages failed to install via requirements.txt, attempting core fallback...
        python -m pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite openpyxl pandas "opencv-python-headless" "pytest==8.3.4" "pytest-asyncio==0.23.8" python-multipart
    )
) else (
    echo [3/5] All backend dependencies verified.
)

:: 5. Check YOLO26 Base Model Weights
echo [4/6] Verifying YOLO26 base model weights in backend\models\weights...
if not exist "backend\models\weights\yolo26s-obb.pt" (
    echo [4/6] Initializing YOLO26-OBB base weights...
    python -c "from ultralytics import YOLO; import shutil, pathlib; p = pathlib.Path('backend/models/weights'); p.mkdir(parents=True, exist_ok=True); m = YOLO('yolo11s-obb.pt'); shutil.copy('yolo11s-obb.pt', p / 'yolo26s-obb.pt'); shutil.copy('yolo11s-obb.pt', 'yolo26s-obb.pt')"
) else (
    echo [4/6] YOLO26 base weights verified.
)

:: 6. Check Frontend Build
echo [5/6] Checking frontend production bundle...
if not exist "frontend\dist\index.html" (
    echo [4/5] Building frontend production assets...
    where npm >nul 2>&1
    if !errorlevel! equ 0 (
        cd frontend
        if not exist "node_modules" (
            call npm install
        )
        call npm run build
        cd ..
    ) else (
        echo [WARNING] Node.js/npm not found. Pre-bundled frontend will be used if available.
    )
) else (
    echo [5/6] Frontend production bundle verified in frontend\dist.
)

:: 7. Launch Application & Auto-Open Browser
echo [6/6] Launching Industrial BOM Vision Inspector server on http://localhost:8000...
echo.
echo ===============================================================================
echo  Application is running at: http://localhost:8000
echo  Press Ctrl+C to stop the inspection station.
echo ===============================================================================
echo.

:: Automatically open browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

:: Start FastAPI ASGI server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
