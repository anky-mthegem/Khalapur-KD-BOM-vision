import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  Camera,
  Sparkles,
  Save,
  Play,
  CheckCircle2,
  Trash2,
  FolderOpen,
  Layers,
  Cpu,
  AlertTriangle,
  RefreshCw,
  Zap,
  Image as ImageIcon,
  Crosshair,
  Maximize2,
  RotateCcw,
  Square
} from 'lucide-react';
import { api } from '../../services/api';
import { PartCatalogItem, DatasetSummary, TrainingStatus, BomRecipe } from '../../types/bom';

interface ProposalBox {
  id: string;
  polygon: number[][]; // [[x1, y1], [x2, y2], [x3, y3], [x4, y4]] normalized
  center: [number, number];
  width: number;
  height: number;
  angle: number;
  area: number;
  part_uid: string;
  item_name?: string;
}

interface LabelingStudioTabProps {
  activeMasterCode: string;
}

export const LabelingStudioTab: React.FC<LabelingStudioTabProps> = ({
  activeMasterCode
}) => {
  // Image & Canvas state
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [currentFilename, setCurrentFilename] = useState<string>('sample.jpg');
  const [proposals, setProposals] = useState<ProposalBox[]>([]);
  const [selectedItemName, setSelectedItemName] = useState<string>('');
  const [selectedDrawingNo, setSelectedDrawingNo] = useState<string>('');

  // Interactive Click & Drag Drawing State
  const [isDrawing, setIsDrawing] = useState(false);
  const [dragStart, setDragStart] = useState<{ nx: number; ny: number } | null>(null);
  const [draftPolygon, setDraftPolygon] = useState<number[][] | null>(null);

  // Data & Dataset state
  const [parts, setParts] = useState<PartCatalogItem[]>([]);
  const [activeRecipe, setActiveRecipe] = useState<BomRecipe | null>(null);
  const [datasetSummary, setDatasetSummary] = useState<DatasetSummary | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Training state
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
  const [isStartingTraining, setIsStartingTraining] = useState(false);
  const [showTrainingPanel, setShowTrainingPanel] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageObjRef = useRef<HTMLImageElement | null>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // 1. Initial Load: Parts catalog, active recipe items, dataset summary, and training status
  const loadData = async () => {
    try {
      const [partsList, summary, trainStatus] = await Promise.all([
        api.listParts(),
        api.getDatasetSummary(),
        api.getTrainingStatus()
      ]);
      setParts(partsList);
      setDatasetSummary(summary);
      setTrainingStatus(trainStatus);

      if (activeMasterCode) {
        try {
          const recipe = await api.getRecipe(activeMasterCode);
          setActiveRecipe(recipe);
          // Default selection to first vision inspected item
          const firstVision = recipe.items.find((it) => it.is_vision_inspected);
          if (firstVision && !selectedItemName) {
            setSelectedItemName(firstVision.item_name);
            setSelectedDrawingNo(firstVision.drawing_no);
          }
        } catch (e) {
          console.warn("Could not load recipe details for", activeMasterCode);
        }
      }
    } catch (e) {
      console.error("Error loading labeling data:", e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(async () => {
      try {
        const st = await api.getTrainingStatus();
        setTrainingStatus(st);
        if (st.status === 'RUNNING') {
          setShowTrainingPanel(true);
        }
      } catch (e) {
        // quiet poll
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeMasterCode]);

  useEffect(() => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [trainingStatus?.logs]);

  // 2. Handle Image File Selection (Browse button)
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setCurrentFilename(file.name);
      setIsProcessing(true);
      setNotification(null);

      try {
        const res = await api.uploadComponentImage(file);
        setImageBase64(res.image_base64);

        // If backend returned contour proposals, use them; otherwise create default centered box
        let boxes = res.proposals || [];
        if (boxes.length === 0) {
          boxes = [{
            id: 'box_default',
            polygon: [[0.15, 0.15], [0.85, 0.15], [0.85, 0.85], [0.15, 0.85]],
            center: [0.5, 0.5],
            width: 0.7,
            height: 0.7,
            angle: 0,
            area: 0.49,
            part_uid: selectedDrawingNo || selectedItemName,
            item_name: selectedItemName
          }];
        } else {
          boxes = boxes.map((b: any) => ({
            ...b,
            item_name: selectedItemName,
            part_uid: selectedDrawingNo || selectedItemName
          }));
        }

        setProposals(boxes);

        const img = new Image();
        img.src = res.image_base64;
        img.onload = () => {
          imageObjRef.current = img;
          drawCanvas(boxes);
        };
      } catch (err: any) {
        setNotification({ type: 'error', message: 'Failed to read image: ' + err.message });
      } finally {
        setIsProcessing(false);
      }
    }
  };

  // 3. Optional: Capture from Live Camera
  const handleCaptureCamera = async () => {
    setIsProcessing(true);
    setNotification(null);
    try {
      const data = await api.captureFrame();
      setImageBase64(data.image_base64);
      setCurrentFilename(`camera_capture_${Date.now()}.jpg`);

      const boxes = (data.proposals || []).map((b: any) => ({
        ...b,
        item_name: selectedItemName,
        part_uid: selectedDrawingNo || selectedItemName
      }));
      setProposals(boxes);

      const img = new Image();
      img.src = data.image_base64;
      img.onload = () => {
        imageObjRef.current = img;
        drawCanvas(boxes);
      };
    } catch (e: any) {
      setNotification({ type: 'error', message: 'Camera frame capture failed: ' + e.message });
    } finally {
      setIsProcessing(false);
    }
  };

  // 4. One-Click Box Utilities
  const handleAutoContours = async () => {
    if (!imageBase64) return;
    setIsProcessing(true);
    try {
      const data = await api.autoAnnotate(60, 5, 200, 50000);
      const boxes = (data.proposals || []).map((b: any) => ({
        ...b,
        item_name: selectedItemName,
        part_uid: selectedDrawingNo || selectedItemName
      }));
      setProposals(boxes);
      drawCanvas(boxes);
      setNotification({ type: 'success', message: `OpenCV auto-detected ${boxes.length} box(es).` });
    } catch (e: any) {
      setNotification({ type: 'error', message: 'Auto-contour failed: ' + e.message });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSetFullImageBox = () => {
    if (!imageBase64) return;
    const fullBox: ProposalBox = {
      id: `box_full_${Date.now()}`,
      polygon: [[0.05, 0.05], [0.95, 0.05], [0.95, 0.95], [0.05, 0.95]],
      center: [0.5, 0.5],
      width: 0.9,
      height: 0.9,
      angle: 0,
      area: 0.81,
      part_uid: selectedDrawingNo || selectedItemName,
      item_name: selectedItemName
    };
    setProposals([fullBox]);
    drawCanvas([fullBox]);
    setNotification({ type: 'success', message: 'Box set to cover the component frame.' });
  };

  const handleClearBox = () => {
    setProposals([]);
    drawCanvas([]);
    setNotification({ type: 'success', message: 'Box cleared. Click and drag on the image to draw a new box.' });
  };

  // 5. Interactive Mouse Coordinates Helper
  const getNormalizedCoordinates = (e: React.MouseEvent<HTMLCanvasElement>): { nx: number; ny: number } => {
    const canvas = canvasRef.current;
    if (!canvas) return { nx: 0, ny: 0 };
    const rect = canvas.getBoundingClientRect();
    const nx = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const ny = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
    return { nx, ny };
  };

  // 6. Interactive Click & Drag Handlers
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!imageBase64) return;
    e.preventDefault();
    const { nx, ny } = getNormalizedCoordinates(e);
    setIsDrawing(true);
    setDragStart({ nx, ny });
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !dragStart || !canvasRef.current || !imageObjRef.current) return;
    const { nx, ny } = getNormalizedCoordinates(e);

    const x1 = Math.min(dragStart.nx, nx);
    const y1 = Math.min(dragStart.ny, ny);
    const x2 = Math.max(dragStart.nx, nx);
    const y2 = Math.max(dragStart.ny, ny);

    const draftPoly = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]];
    setDraftPolygon(draftPoly);

    // Live redraw with active draft box
    drawCanvas(proposals, draftPoly);
  };

  const handleCanvasMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !dragStart) return;
    const { nx, ny } = getNormalizedCoordinates(e);

    const x1 = Math.min(dragStart.nx, nx);
    const y1 = Math.min(dragStart.ny, ny);
    const x2 = Math.max(dragStart.nx, nx);
    const y2 = Math.max(dragStart.ny, ny);

    const width = x2 - x1;
    const height = y2 - y1;

    // Minimum size threshold (2% of image dimension) to prevent accidental clicks
    if (width > 0.02 && height > 0.02) {
      const newBox: ProposalBox = {
        id: `box_user_${Date.now()}`,
        polygon: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
        center: [(x1 + x2) / 2, (y1 + y2) / 2],
        width,
        height,
        angle: 0,
        area: width * height,
        part_uid: selectedDrawingNo || selectedItemName,
        item_name: selectedItemName
      };

      const updated = [newBox];
      setProposals(updated);
      drawCanvas(updated, null);
      setNotification({
        type: 'success',
        message: `Created box (${Math.round(width * 100)}% × ${Math.round(height * 100)}%). Ready to add to training folder.`
      });
    }

    setIsDrawing(false);
    setDragStart(null);
    setDraftPolygon(null);
  };

  // 7. Draw Canvas with High-Contrast Bounding Box, Corner Handles & Label Banner
  const drawCanvas = (boxes: ProposalBox[], activeDraft: number[][] | null = null) => {
    const canvas = canvasRef.current;
    if (!canvas || !imageObjRef.current) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = imageObjRef.current.width;
    canvas.height = imageObjRef.current.height;

    // 1. Draw base photo
    ctx.drawImage(imageObjRef.current, 0, 0);

    // 2. Draw confirmed boxes
    boxes.forEach((b) => {
      const pts = b.polygon.map(([nx, ny]) => [nx * canvas.width, ny * canvas.height]);
      if (pts.length >= 4) {
        ctx.beginPath();
        ctx.lineWidth = 3;
        ctx.strokeStyle = '#107C10'; // Plant Green

        ctx.moveTo(pts[0][0], pts[0][1]);
        for (let i = 1; i < pts.length; i++) {
          ctx.lineTo(pts[i][0], pts[i][1]);
        }
        ctx.closePath();
        ctx.stroke();

        // Translucent highlight fill
        ctx.fillStyle = 'rgba(16, 124, 16, 0.18)';
        ctx.fill();

        // Corner grab handle circles
        pts.forEach(([px, py]) => {
          ctx.beginPath();
          ctx.arc(px, py, 5, 0, Math.PI * 2);
          ctx.fillStyle = '#FFFFFF';
          ctx.fill();
          ctx.lineWidth = 2;
          ctx.strokeStyle = '#107C10';
          ctx.stroke();
        });

        // Top label badge
        const cx = Math.min(...pts.map((p) => p[0]));
        const cy = Math.min(...pts.map((p) => p[1]));
        const labelText = selectedItemName ? selectedItemName.slice(0, 36) : 'SELECT ITEM NAME (LABEL)';

        ctx.fillStyle = '#107C10';
        ctx.fillRect(Math.max(10, cx), Math.max(18, cy - 22), 240, 22);
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 11px sans-serif';
        ctx.fillText(labelText, Math.max(14, cx + 4), Math.max(34, cy - 7));
      }
    });

    // 3. Draw live click-and-drag draft box (if currently dragging)
    if (activeDraft && activeDraft.length >= 4) {
      const draftPts = activeDraft.map(([nx, ny]) => [nx * canvas.width, ny * canvas.height]);
      ctx.beginPath();
      ctx.lineWidth = 3;
      ctx.setLineDash([8, 4]); // Dashed line while drawing
      ctx.strokeStyle = '#00E5FF'; // Vibrant Cyan for live drag

      ctx.moveTo(draftPts[0][0], draftPts[0][1]);
      for (let i = 1; i < draftPts.length; i++) {
        ctx.lineTo(draftPts[i][0], draftPts[i][1]);
      }
      ctx.closePath();
      ctx.stroke();
      ctx.setLineDash([]); // Reset dash

      ctx.fillStyle = 'rgba(0, 229, 255, 0.15)';
      ctx.fill();

      // Dimension guide badge
      const dw = Math.abs(draftPts[1][0] - draftPts[0][0]);
      const dh = Math.abs(draftPts[2][1] - draftPts[1][1]);
      const minX = Math.min(...draftPts.map((p) => p[0]));
      const minY = Math.min(...draftPts.map((p) => p[1]));

      ctx.fillStyle = '#004B50';
      ctx.fillRect(minX, Math.max(10, minY - 18), 120, 18);
      ctx.fillStyle = '#00E5FF';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(`${Math.round(dw)} × ${Math.round(dh)} px`, minX + 6, Math.max(24, minY - 5));
    }
  };

  // 8. Save Component Image & Label to Training Folder
  const handleSaveToTraining = async () => {
    if (!imageBase64) {
      setNotification({ type: 'error', message: 'Please browse or capture a component image first.' });
      return;
    }
    if (!selectedItemName) {
      setNotification({ type: 'error', message: 'Please select an Item Name from the BOM dropdown on the right.' });
      return;
    }
    if (proposals.length === 0) {
      setNotification({ type: 'error', message: 'Please create a box around the object first (click & drag on image, or click "Auto Box").' });
      return;
    }

    setIsProcessing(true);
    setNotification(null);

    try {
      const activePolygon = proposals[0].polygon;

      await api.saveComponent({
        image_base64: imageBase64,
        item_name: selectedItemName,
        drawing_no: selectedDrawingNo,
        polygon: activePolygon,
        master_item_code: activeMasterCode
      });

      setNotification({
        type: 'success',
        message: `Saved component image for "${selectedItemName}" directly into training folder!`
      });

      // Refresh dataset summary and parts catalog counts
      const [newSummary, partsList] = await Promise.all([
        api.getDatasetSummary(),
        api.listParts()
      ]);
      setDatasetSummary(newSummary);
      setParts(partsList);
    } catch (e: any) {
      setNotification({ type: 'error', message: 'Error saving component: ' + e.message });
    } finally {
      setIsProcessing(false);
    }
  };

  // 9. Delete sample from training folder
  const handleDeleteSample = async (stem: string) => {
    try {
      await api.deleteSample(stem);
      const summary = await api.getDatasetSummary();
      setDatasetSummary(summary);
      setNotification({ type: 'success', message: `Deleted sample '${stem}' from training folder.` });
    } catch (e: any) {
      setNotification({ type: 'error', message: 'Failed to delete sample: ' + e.message });
    }
  };

  // 10. Trigger YOLO26 Model Training
  const handleStartTraining = async () => {
    setIsStartingTraining(true);
    setShowTrainingPanel(true);
    setNotification(null);
    try {
      await api.startTraining({
        base_model: "yolo26s-obb.pt",
        epochs: 50,
        imgsz: 1280,
        device: "auto"
      });
      const st = await api.getTrainingStatus();
      setTrainingStatus(st);
    } catch (e: any) {
      setNotification({ type: 'error', message: 'Error initiating training: ' + e.message });
    } finally {
      setIsStartingTraining(false);
    }
  };

  // Available label items
  const availableItems = activeRecipe
    ? activeRecipe.items.filter((it) => it.is_vision_inspected)
    : parts.map((p, idx) => ({
        sr_no: idx + 1,
        item_name: p.item_name,
        drawing_no: p.drawing_no,
        target_qty: 1,
        is_vision_inspected: true
      }));

  const isTraining = trainingStatus?.status === 'RUNNING';
  const isCompleted = trainingStatus?.status === 'COMPLETED';
  const progressPct = trainingStatus && trainingStatus.total_epochs > 0
    ? (trainingStatus.current_epoch / trainingStatus.total_epochs) * 100
    : 0;

  return (
    <div className="flex-1 bg-[#F3F2F1] flex flex-col overflow-hidden text-xs select-none">
      {/* 1. Top Ribbon Action Bar */}
      <div className="bg-white border-b border-[#D2D0CE] px-4 py-2 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-2">
          {/* Browse Image Button */}
          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isProcessing || isTraining}
            className="px-3.5 py-1.5 bg-[#107C41] hover:bg-[#0E6032] text-white rounded font-bold flex items-center space-x-1.5 shadow transition"
            title="Browse and select a component image file from your computer"
          >
            <FolderOpen className="w-4 h-4 text-yellow-300" />
            <span>Browse Component Image</span>
          </button>

          {/* Capture from Camera */}
          <button
            onClick={handleCaptureCamera}
            disabled={isProcessing || isTraining}
            className="px-3 py-1.5 bg-[#2B579A] hover:bg-[#1E3E6D] text-white rounded font-semibold flex items-center space-x-1.5"
            title="Grab current frame from conveyor camera"
          >
            <Camera className="w-4 h-4" />
            <span>Camera Capture</span>
          </button>

          <div className="ribbon-divider" />

          {/* BOX CREATION TOOLS */}
          <div className="flex items-center space-x-1 bg-gray-100 p-0.5 rounded border border-gray-300">
            {/* Draw Box / Click & Drag Tool */}
            <button
              onClick={() => {
                setNotification({
                  type: 'success',
                  message: 'Draw Box Active: Click and drag with your mouse directly on the image to outline the component.'
                });
              }}
              className="px-3 py-1 bg-white hover:bg-cyan-50 border border-cyan-400 text-cyan-900 rounded font-bold flex items-center space-x-1 shadow-sm"
              title="Click and drag with mouse on the image to draw a bounding box around any hardware piece"
            >
              <Crosshair className="w-3.5 h-3.5 text-cyan-700" />
              <span>Click & Drag Box</span>
            </button>

            {/* Auto Fastener Contours (OpenCV) */}
            <button
              onClick={handleAutoContours}
              disabled={!imageBase64 || isProcessing || isTraining}
              className="px-2.5 py-1 text-gray-700 hover:text-purple-800 hover:bg-purple-50 rounded font-semibold flex items-center space-x-1 disabled:opacity-40"
              title="Use OpenCV adaptive contour detection to automatically find the fastener's oriented bounding box"
            >
              <Sparkles className="w-3.5 h-3.5 text-purple-600" />
              <span>Auto Box</span>
            </button>

            {/* Full Image Box */}
            <button
              onClick={handleSetFullImageBox}
              disabled={!imageBase64 || isProcessing || isTraining}
              className="px-2.5 py-1 text-gray-700 hover:text-blue-800 hover:bg-blue-50 rounded font-semibold flex items-center space-x-1 disabled:opacity-40"
              title="Fit bounding box around the whole component frame"
            >
              <Maximize2 className="w-3.5 h-3.5 text-blue-600" />
              <span>Full Box</span>
            </button>

            {/* Clear Box */}
            <button
              onClick={handleClearBox}
              disabled={!imageBase64 || proposals.length === 0 || isProcessing || isTraining}
              className="px-2 py-1 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded font-semibold disabled:opacity-40"
              title="Remove existing box so you can redraw a new one"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="ribbon-divider" />

          {/* Save & Add to Training Folder */}
          <button
            onClick={handleSaveToTraining}
            disabled={!imageBase64 || proposals.length === 0 || isProcessing || isTraining}
            className="px-4 py-1.5 bg-[#107C10] hover:bg-[#0E6A0E] text-white rounded font-bold flex items-center space-x-1.5 shadow disabled:opacity-50"
            title="Store labeled image and annotation txt in training folder"
          >
            <Save className="w-4 h-4 text-white" />
            <span>Add to Training Folder</span>
          </button>

          {/* Notification Message */}
          {notification && (
            <div
              className={`flex items-center space-x-1.5 px-3 py-1 rounded border font-semibold ${
                notification.type === 'success'
                  ? 'bg-green-50 text-[#107C10] border-green-300'
                  : 'bg-red-50 text-red-700 border-red-300'
              }`}
            >
              {notification.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <AlertTriangle className="w-4 h-4" />
              )}
              <span>{notification.message}</span>
            </div>
          )}
        </div>

        {/* Start Training Button */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleStartTraining}
            disabled={isTraining || isStartingTraining}
            className={`px-4 py-1.5 rounded font-extrabold text-white flex items-center space-x-1.5 shadow transition ${
              isTraining
                ? 'bg-amber-600 animate-pulse cursor-not-allowed'
                : 'bg-[#2B579A] hover:bg-[#1E3E6D]'
            }`}
            title="Trigger YOLO26 model training on all images stored in the training folder"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>{isTraining ? 'Training in Progress...' : 'Start YOLO26 Model Training'}</span>
          </button>
        </div>
      </div>

      {/* 2. Main Workspace Split */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left (60%): Interactive Component Annotation Canvas */}
        <div className="flex-1 bg-black flex flex-col items-center justify-center p-3 relative overflow-hidden">
          {imageBase64 ? (
            <div className="relative max-h-full max-w-full flex flex-col items-center justify-center overflow-auto">
              {/* Interactive Helper Prompt Banner */}
              <div className="absolute top-3 left-4 right-4 z-20 flex justify-between items-center pointer-events-none">
                <div className="bg-[#107C41]/95 text-white px-3 py-1 rounded shadow-md border border-green-400 text-xs flex items-center space-x-2">
                  <Crosshair className="w-4 h-4 text-yellow-300" />
                  <span className="font-bold">
                    Box Creator Active: Click and drag with mouse to draw a box around the object.
                  </span>
                </div>
                {proposals.length > 0 && (
                  <div className="bg-black/80 text-green-400 px-2.5 py-1 rounded text-[11px] font-mono border border-green-600">
                    Box: {Math.round(proposals[0].width * 100)}% × {Math.round(proposals[0].height * 100)}%
                  </div>
                )}
              </div>

              {/* Canvas with Mouse Drag Event Handlers */}
              <canvas
                ref={canvasRef}
                onMouseDown={handleCanvasMouseDown}
                onMouseMove={handleCanvasMouseMove}
                onMouseUp={handleCanvasMouseUp}
                onMouseLeave={handleCanvasMouseUp}
                className="max-h-full max-w-full object-contain border-2 border-gray-600 rounded shadow cursor-crosshair"
              />

              {/* Bottom Image Info Badge */}
              <div className="absolute bottom-2 left-2 bg-black/80 text-white px-2.5 py-1 rounded text-[11px] font-mono border border-gray-600">
                Image: {currentFilename} | Assigned Label: <span className="text-yellow-300 font-bold">{selectedItemName || "NONE (SELECT ON RIGHT)"}</span>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400 p-8 space-y-3">
              <ImageIcon className="w-16 h-16 mx-auto text-gray-600" />
              <p className="text-sm font-semibold">No Component Image Loaded</p>
              <p className="text-xs text-gray-500 max-w-md">
                Click <strong>"Browse Component Image"</strong> above to select an image from your computer, or click <strong>"Camera Capture"</strong> to grab from the live conveyor.
              </p>
            </div>
          )}
        </div>

        {/* Right (40%): Label Selector, Training Folder Summary & Live Console */}
        <div className="w-[440px] bg-white border-l border-[#D2D0CE] flex flex-col h-full overflow-hidden">
          {/* Header */}
          <div className="p-3 bg-gray-50 border-b border-gray-200">
            <h3 className="font-bold text-gray-800 text-xs uppercase tracking-wider flex items-center space-x-1.5">
              <Layers className="w-4 h-4 text-[#2B579A]" />
              <span>Standard Excel BOM Label Selector</span>
            </h3>
            <p className="text-[11px] text-gray-500 mt-0.5">
              Select the Item Name from the active BOM to act as the ground-truth YOLO26 label.
            </p>
          </div>

          {/* Active Item Name Selector */}
          <div className="p-3 border-b border-gray-200 bg-white space-y-2">
            <label className="font-bold text-gray-700 block text-xs">
              Item Name (YOLO Class Label):
            </label>
            <select
              value={selectedItemName}
              onChange={(e) => {
                const name = e.target.value;
                setSelectedItemName(name);
                const matched = availableItems.find((it) => it.item_name === name);
                setSelectedDrawingNo(matched ? matched.drawing_no : '');
                // Update boxes on canvas
                const updated = proposals.map((b) => ({ ...b, item_name: name, part_uid: matched?.drawing_no || name }));
                setProposals(updated);
                drawCanvas(updated);
              }}
              className="w-full p-2 border border-gray-300 rounded font-sans text-xs bg-gray-50 focus:bg-white font-medium text-gray-900 focus:outline-none focus:border-[#2B579A]"
            >
              <option value="">-- Choose BOM Component Label --</option>
              {availableItems.map((it) => {
                const sampleCount = datasetSummary?.parts_summary.find((p) => p.item_name === it.item_name)?.sample_count || 0;
                return (
                  <option key={it.item_name} value={it.item_name}>
                    #{it.sr_no} | {it.item_name} {it.drawing_no !== '—' ? `[${it.drawing_no}]` : ''} ({sampleCount} in training folder)
                  </option>
                );
              })}
            </select>

            {selectedItemName && (
              <div className="bg-blue-50 border border-blue-200 p-2 rounded text-[11px] text-blue-900 flex justify-between items-center">
                <div>
                  <span className="font-semibold">Drawing No:</span> {selectedDrawingNo || '—'}<br />
                  <span className="font-semibold">Target BOM Qty:</span> {availableItems.find((it) => it.item_name === selectedItemName)?.target_qty || 1} pcs
                </div>
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold text-blue-700 block">Collected</span>
                  <span className="text-sm font-extrabold font-mono text-[#107C10]">
                    {datasetSummary?.parts_summary.find((p) => p.item_name === selectedItemName)?.sample_count || 0} images
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Middle: Training Folder Summary & Gallery */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-bold text-gray-800 text-xs">
                Training Folder Dataset ({datasetSummary?.total_images || 0} images)
              </span>
              <button
                onClick={loadData}
                className="text-[11px] text-[#2B579A] hover:underline flex items-center space-x-1"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>
            </div>

            {/* BOM Components Sample Progress Table */}
            <div className="border border-gray-200 rounded overflow-hidden">
              <table className="excel-grid-table">
                <thead>
                  <tr>
                    <th>Item Name (Label)</th>
                    <th className="w-16 text-center">Images</th>
                    <th className="w-16 text-center">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(datasetSummary?.parts_summary || []).map((p) => (
                    <tr
                      key={p.item_name}
                      onClick={() => {
                        setSelectedItemName(p.item_name);
                        setSelectedDrawingNo(p.drawing_no);
                      }}
                      className={`cursor-pointer ${p.item_name === selectedItemName ? 'bg-cyan-50 font-semibold' : 'hover:bg-gray-50'}`}
                    >
                      <td className="truncate max-w-[200px]" title={p.item_name}>
                        {p.item_name}
                      </td>
                      <td className="text-center font-mono font-bold">
                        {p.sample_count}
                      </td>
                      <td className="text-center">
                        <span
                          className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${
                            p.sample_count > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {p.sample_count > 0 ? 'READY' : 'EMPTY'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Recent Stored Images in Training Folder */}
            <div className="space-y-1.5 pt-1">
              <span className="font-semibold text-gray-700 text-[11px] block">
                Recently Saved Images:
              </span>
              <div className="space-y-1 max-h-40 overflow-y-auto border border-gray-200 rounded p-1 bg-gray-50">
                {(datasetSummary?.samples || []).map((s) => (
                  <div
                    key={s.filename}
                    className="flex items-center justify-between p-1.5 bg-white border border-gray-200 rounded text-[11px]"
                  >
                    <div className="truncate max-w-[280px]">
                      <span className="font-mono text-gray-500 text-[10px] block truncate">{s.filename}</span>
                      <strong className="text-[#107C10] font-sans truncate block">{s.primary_label}</strong>
                    </div>
                    <button
                      onClick={() => handleDeleteSample(s.stem)}
                      className="text-gray-400 hover:text-red-600 p-1"
                      title="Delete from training folder"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
                {(!datasetSummary?.samples || datasetSummary.samples.length === 0) && (
                  <div className="text-center py-4 text-gray-400 italic text-[11px]">
                    No images saved yet. Browse an image and click "Add to Training Folder".
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Bottom: Live Training Progress & Terminal Logs */}
          <div className="border-t border-gray-300 bg-gray-900 text-gray-200 p-3 space-y-2">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-1.5">
                <Cpu className="w-4 h-4 text-yellow-300" />
                <span className="font-bold text-xs uppercase text-white">
                  YOLO26 Training Engine:
                </span>
                <span
                  className={`font-mono font-bold text-[11px] px-1.5 py-0.2 rounded ${
                    isTraining
                      ? 'bg-amber-600 text-white animate-pulse'
                      : isCompleted
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  {trainingStatus?.status || 'IDLE'}
                </span>
              </div>
              <span className="font-mono text-[11px] text-gray-300">
                Epoch: <strong>{trainingStatus?.current_epoch || 0} / {trainingStatus?.total_epochs || 50}</strong>
              </span>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
              <div
                className="bg-green-500 h-full transition-all duration-300"
                style={{ width: `${progressPct}%` }}
              />
            </div>

            {/* Live Terminal Console Logs */}
            <div
              ref={logsContainerRef}
              className="bg-black/90 rounded border border-gray-700 p-2 h-28 overflow-y-auto font-mono text-[10px] text-green-400 leading-tight space-y-0.5"
            >
              {(trainingStatus?.logs && trainingStatus.logs.length > 0) ? (
                trainingStatus.logs.map((line, idx) => (
                  <div key={idx} className="whitespace-pre-wrap">{line}</div>
                ))
              ) : (
                <div className="text-gray-500 italic">
                  Training logs console ready. Click "Start YOLO26 Model Training" above to begin.
                </div>
              )}
            </div>

            {/* Completion Banner */}
            {isCompleted && (
              <div className="bg-green-900/80 border border-green-500 text-white p-2 rounded text-[11px] flex items-center justify-between">
                <span className="flex items-center space-x-1 font-bold">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  <span>Training finished! Active weights: {trainingStatus?.active_weights}</span>
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
