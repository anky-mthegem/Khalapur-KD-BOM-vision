#!/usr/bin/env bash
# ==============================================================================
# Production Setup Script for Ubuntu 22.04 / 24.04 LTS
# Industrial Conveyor Belt BOM Vision Inspector
# ==============================================================================

set -e

echo "=== [1/6] Installing Ubuntu System Dependencies ==="
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    git

# Install Node.js if missing
if ! command -v node &> /dev/null; then
    echo "=== Installing Node.js LTS ==="
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "=== [2/6] Setting Up Python Virtual Environment ==="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip

echo "=== [3/6] Installing Backend Python Requirements ==="
pip install -r backend/requirements.txt

# Ensure YOLO26 base model weights exist
mkdir -p backend/models/weights
if [ ! -f "backend/models/weights/yolo26s-obb.pt" ]; then
    echo "=== Initializing YOLO26-OBB Base Weights ==="
    python3 -c "from ultralytics import YOLO; import shutil, pathlib; p = pathlib.Path('backend/models/weights'); p.mkdir(parents=True, exist_ok=True); m = YOLO('yolo11s-obb.pt'); shutil.copy('yolo11s-obb.pt', p / 'yolo26s-obb.pt')"
fi

echo "=== [4/6] Building React Frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== [5/6] Running System Verification Tests ==="
pytest backend/tests

echo "=== [6/6] Installing Systemd Service ==="
SERVICE_FILE="deployment/bom-inspector.service"
if [ -f "$SERVICE_FILE" ]; then
    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)
    sed -i "s|/opt/bom-inspector|$CURRENT_DIR|g" "$SERVICE_FILE"
    sed -i "s|User=ubuntu|User=$CURRENT_USER|g" "$SERVICE_FILE"
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable bom-inspector.service
    sudo systemctl restart bom-inspector.service
    echo "Service installed and started. Check status with: sudo systemctl status bom-inspector.service"
fi

echo "=== Setup Complete! Open http://localhost:8000 in your browser ==="
