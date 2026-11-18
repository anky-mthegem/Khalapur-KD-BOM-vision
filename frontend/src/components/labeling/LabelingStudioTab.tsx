import React, { useState, useEffect, useRef, useCallback, useImperativeHandle } from 'react';
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
  Square,
  ZoomIn,
  ZoomOut,
  Move,
  Eye,
  EyeOff,
  ChevronLeft,
  ChevronRight,
  HelpCircle,
  Tag,
  Check,
  MousePointer,
  RotateCw
} from 'lucide-react';
import { api } from '../../services/api';
import { PartCatalogItem, DatasetSummary, TrainingStatus, BomRecipe } from '../../types/bom';

// 12 Distinct High-Contrast Industrial Label Palette Colors (Label Studio Style)
const LABEL_COLORS = [
  '#107C10', // Green
  '#0078D4', // Blue
  '#D13438', // Red
  '#8764B8', // Violet
  '#008272', // Teal
  '#E3008C', // Magenta
  '#FF8C00', // Orange
  '#004E8C', // Navy
  '#498205', // Olive
  '#00B7C3', // Cyan
  '#A80000', // Dark Red
  '#6B69D6', // Iris
];

export const getLabelColor = (index: number) => LABEL_COLORS[index % LABEL_COLORS.length];

export interface AnnotationRegion {
  id: string;
  item_name: string;
  part_uid: string;
  drawing_no: string;
  color: string;
  // Normalized coordinates (0.0 to 1.0)
  x: number;
  y: number;
  width: number;
  height: number;
  angle: number; // in degrees for OBB
  polygon: number[][]; // 4 points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
  is_visible: boolean;
}

interface ImageQueueItem {
  id: string;
  name: string;
  base64: string;
  file?: File;
  regions: AnnotationRegion[];
}

export type ActiveTool = 'rect' | 'obb' | 'select' | 'pan';

export interface LabelingStudioTabRef {
  captureFrame: () => Promise<void>;
  autoAnnotate: () => Promise<void>;
  saveAnnotations: () => Promise<void>;
}

export interface LabelingStudioTabProps {
  activeMasterCode: string;
}

export const LabelingStudioTab = React.forwardRef<LabelingStudioTabRef, LabelingStudioTabProps>(({
  activeMasterCode
}, ref) => {
  // 1. Tool & Canvas Navigation State (Label Studio Viewport)
  const [activeTool, setActiveTool] = useState<ActiveTool>('rect');
  const [zoom, setZoom] = useState<number>(1.0);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [canvasDisplaySize, setCanvasDisplaySize] = useState<{ width: number; height: number }>({ width: 720, height: 480 });

  // 2. Image Queue State (Batch Filmstrip)
  const [imageQueue, setImageQueue] = useState<ImageQueueItem[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState<number>(0);

  // 3. Current Image & Region Annotations
  const [regions, setRegions] = useState<AnnotationRegion[]>([]);
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);

  // 4. Active Selected Label from BOM
  const [activeLabelIndex, setActiveLabelIndex] = useState<number>(0);
  const [selectedItemName, setSelectedItemName] = useState<string>('');
  const [selectedDrawingNo, setSelectedDrawingNo] = useState<string>('');

  // 5. Drawing & Dragging State
  const [isDrawing, setIsDrawing] = useState(false);
  const [dragStart, setDragStart] = useState<{ nx: number; ny: number } | null>(null);
  const [draftRect, setDraftRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);

  // 6. Resizing / Moving Existing Region
  const [isTransforming, setIsTransforming] = useState(false);
  const [transformHandle, setTransformHandle] = useState<string | null>(null); // 'tl', 'tr', 'br', 'bl', 'rotate', 'move'
  const [transformStart, setTransformStart] = useState<{ nx: number; ny: number; initialRegion: AnnotationRegion } | null>(null);

  // 7. Data & Dataset State
  const [parts, setParts] = useState<PartCatalogItem[]>([]);
  const [activeRecipe, setActiveRecipe] = useState<BomRecipe | null>(null);
  const [datasetSummary, setDatasetSummary] = useState<DatasetSummary | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  // 8. Training State
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
  const [isStartingTraining, setIsStartingTraining] = useState(false);
  const [showTrainingPanel, setShowTrainingPanel] = useState(false);

  // DOM Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageObjRef = useRef<HTMLImageElement | null>(null);
  const viewportContainerRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Current Active Image in Queue
  const currentImage = imageQueue[currentImageIndex] || null;

  // Load Parts & Recipes
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

  // Available label items from BOM
  const availableItems = activeRecipe
    ? activeRecipe.items.filter((it) => it.is_vision_inspected)
    : parts.map((p, idx) => ({
        sr_no: idx + 1,
        item_name: p.item_name,
        drawing_no: p.drawing_no,
        target_qty: 1,
        is_vision_inspected: true
      }));

  // Auto-select first label if none chosen
  useEffect(() => {
    if (availableItems.length > 0 && !selectedItemName) {
      setSelectedItemName(availableItems[0].item_name);
      setSelectedDrawingNo(availableItems[0].drawing_no || '');
      setActiveLabelIndex(0);
    }
  }, [availableItems, selectedItemName]);

  // Calculate responsive fit scale so image fits 100% within viewport container
  const fitImageToContainer = useCallback(() => {
    if (!imageObjRef.current || !viewportContainerRef.current) return;
    const container = viewportContainerRef.current;
    const paddingX = 48;
    const paddingY = 64; // account for top floating zoom control pill
    const availW = Math.max(200, container.clientWidth - paddingX);
    const availH = Math.max(200, container.clientHeight - paddingY);

    const imgW = imageObjRef.current.width || 800;
    const imgH = imageObjRef.current.height || 600;

    const scale = Math.min(availW / imgW, availH / imgH);
    const dispW = Math.max(100, Math.round(imgW * scale));
    const dispH = Math.max(100, Math.round(imgH * scale));

    setCanvasDisplaySize({ width: dispW, height: dispH });
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
  }, []);

  // Reset Zoom and Fit to Screen
  const resetZoomAndPan = useCallback(() => {
    fitImageToContainer();
  }, [fitImageToContainer]);

  // Load Active Image onto Canvas
  useEffect(() => {
    if (!currentImage) {
      imageObjRef.current = null;
      setRegions([]);
      setSelectedRegionId(null);
      return;
    }

    const img = new Image();
    img.src = currentImage.base64;
    img.onload = () => {
      imageObjRef.current = img;
      setRegions(currentImage.regions || []);
      setSelectedRegionId(null);
      // Center & fit image completely to viewport
      fitImageToContainer();
      requestAnimationFrame(() => {
        drawCanvas();
      });
    };
  }, [currentImageIndex, imageQueue.length, currentImage?.base64, fitImageToContainer]);

  // Sync active image regions to queue
  useEffect(() => {
    if (imageQueue[currentImageIndex]) {
      imageQueue[currentImageIndex].regions = regions;
    }
  }, [regions, currentImageIndex]);

  // Window resize observer to keep canvas scaled to container
  useEffect(() => {
    const handleResize = () => {
      if (imageObjRef.current) {
        fitImageToContainer();
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [fitImageToContainer]);

  // Redraw Canvas whenever regions, draft, selected box, zoom, pan, or canvasDisplaySize changes
  useEffect(() => {
    drawCanvas();
  }, [regions, draftRect, selectedRegionId, zoom, pan, canvasDisplaySize]);

  // Mouse wheel zoom in / out centered on canvas
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.88;
    setZoom((prevZoom) => {
      const next = Math.max(0.25, Math.min(6.0, prevZoom * zoomFactor));
      return parseFloat(next.toFixed(2));
    });
  };

  // 1. Image File Upload (Browse button - Supports multiple images)
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const files = Array.from(e.target.files);
    setIsProcessing(true);
    setNotification(null);

    const newQueueItems: ImageQueueItem[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const res = await api.uploadComponentImage(file);
        
        // Start with a clean canvas (no phantom auto-boxes).
        // User can manually draw boxes with BBox tool or click "Auto Box" on demand.
        const initialRegions: AnnotationRegion[] = [];

        newQueueItems.push({
          id: `img_${Date.now()}_${i}`,
          name: file.name,
          base64: res.image_base64,
          file,
          regions: initialRegions
        });
      } catch (err: any) {
        console.error("Failed uploading image:", file.name, err);
      }
    }

    if (newQueueItems.length > 0) {
      setImageQueue((prev) => {
        const next = [...prev, ...newQueueItems];
        setCurrentImageIndex(next.length - 1);
        return next;
      });
      setNotification({
        type: 'success',
        message: `Loaded ${newQueueItems.length} image(s). Ready for labeling: select a BOM label above and draw boxes.`
      });
    } else {
      setNotification({ type: 'error', message: 'Failed to read selected image file(s).' });
    }

    setIsProcessing(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // 2. Camera Frame Capture
  const handleCaptureCamera = async () => {
    setIsProcessing(true);
    setNotification(null);
    try {
      const data = await api.captureFrame();
      // Start with a clean canvas so operator can draw or click "Auto Box"
      const initialRegions: AnnotationRegion[] = [];

      const newItem: ImageQueueItem = {
        id: `img_cam_${Date.now()}`,
        name: `conveyor_capture_${Date.now()}.jpg`,
        base64: data.image_base64,
        regions: initialRegions
      };

      setImageQueue((prev) => {
        const next = [...prev, newItem];
        setCurrentImageIndex(next.length - 1);
        return next;
      });
      setNotification({ type: 'success', message: 'Live conveyor frame captured. Select a BOM label and draw boxes.' });
    } catch (e: any) {
      console.error("Camera frame capture failed:", e);
      setNotification({ type: 'error', message: 'Camera frame capture failed: ' + e.message });
    } finally {
      setIsProcessing(false);
    }
  };

  // 3. Label Palette Selector (Hotkeys & Click)
  const handleSelectLabel = (it: any, index: number) => {
    setActiveLabelIndex(index);
    setSelectedItemName(it.item_name);
    setSelectedDrawingNo(it.drawing_no || '');

    // Label Studio feature: If a region is currently selected, immediately update its label!
    if (selectedRegionId) {
      setRegions((prev) =>
        prev.map((r) =>
          r.id === selectedRegionId
            ? {
                ...r,
                item_name: it.item_name,
                part_uid: it.drawing_no || it.item_name,
                drawing_no: it.drawing_no || '',
                color: getLabelColor(index)
              }
            : r
        )
      );
      setNotification({ type: 'info', message: `Updated selected box label to "${it.item_name}"` });
    }
  };

  // 4. Coordinates Mapping (Converts Client Mouse Position to Normalized [0.0 - 1.0] Image Coordinates)
  const getNormalizedPoint = (e: React.MouseEvent<HTMLCanvasElement>): { nx: number; ny: number } => {
    const canvas = canvasRef.current;
    if (!canvas || !imageObjRef.current) return { nx: 0, ny: 0 };
    const rect = canvas.getBoundingClientRect();

    // Map mouse click relative to canvas element
    const canvasX = (e.clientX - rect.left);
    const canvasY = (e.clientY - rect.top);

    const nx = Math.max(0, Math.min(1, canvasX / rect.width));
    const ny = Math.max(0, Math.min(1, canvasY / rect.height));
    return { nx, ny };
  };

  // Check if click hits a region or handle
  const hitTestRegion = (nx: number, ny: number): { region: AnnotationRegion | null; handle: string | null } => {
    if (!imageObjRef.current) return { region: null, handle: null };
    const handleThreshold = 0.03; // ~3% of image width

    // Check selected region's corner handles first
    if (selectedRegionId) {
      const sel = regions.find((r) => r.id === selectedRegionId);
      if (sel) {
        // Handles: tl, tr, br, bl, rotate
        const corners = [
          { handle: 'tl', x: sel.x, y: sel.y },
          { handle: 'tr', x: sel.x + sel.width, y: sel.y },
          { handle: 'br', x: sel.x + sel.width, y: sel.y + sel.height },
          { handle: 'bl', x: sel.x, y: sel.y + sel.height },
          { handle: 'rotate', x: sel.x + sel.width / 2, y: sel.y - 0.04 }
        ];

        for (const c of corners) {
          const dist = Math.hypot(nx - c.x, ny - c.y);
          if (dist < handleThreshold) {
            return { region: sel, handle: c.handle };
          }
        }
      }
    }

    // Check click inside any visible region (reverse order to pick topmost)
    for (let i = regions.length - 1; i >= 0; i--) {
      const r = regions[i];
      if (!r.is_visible) continue;
      if (nx >= r.x && nx <= r.x + r.width && ny >= r.y && ny <= r.y + r.height) {
        return { region: r, handle: 'move' };
      }
    }

    return { region: null, handle: null };
  };

  // 5. Canvas Mouse Events
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!imageObjRef.current) return;

    // Pan with Middle Click or when Pan tool active
    if (activeTool === 'pan' || e.button === 1) {
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
      return;
    }

    const { nx, ny } = getNormalizedPoint(e);

    // If Select Tool Active
    if (activeTool === 'select') {
      const { region, handle } = hitTestRegion(nx, ny);
      if (region) {
        setSelectedRegionId(region.id);
        if (handle) {
          setIsTransforming(true);
          setTransformHandle(handle);
          setTransformStart({ nx, ny, initialRegion: { ...region } });
        }
      } else {
        setSelectedRegionId(null);
      }
      return;
    }

    // If Rectangle (BBox) or OBB Tool Active: Start Drawing
    if (activeTool === 'rect' || activeTool === 'obb') {
      // Check if user clicked an existing region's handle to resize
      const { region, handle } = hitTestRegion(nx, ny);
      if (region && region.id === selectedRegionId && handle && handle !== 'move') {
        setIsTransforming(true);
        setTransformHandle(handle);
        setTransformStart({ nx, ny, initialRegion: { ...region } });
        return;
      }

      setIsDrawing(true);
      setDragStart({ nx, ny });
      setDraftRect({ x: nx, y: ny, w: 0, h: 0 });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isPanning) {
      setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
      return;
    }

    const { nx, ny } = getNormalizedPoint(e);

    // Transforming (Moving / Resizing / Rotating existing region)
    if (isTransforming && transformStart && selectedRegionId) {
      const deltaX = nx - transformStart.nx;
      const deltaY = ny - transformStart.ny;
      const orig = transformStart.initialRegion;

      setRegions((prev) =>
        prev.map((r) => {
          if (r.id !== selectedRegionId) return r;

          let newX = orig.x;
          let newY = orig.y;
          let newW = orig.width;
          let newH = orig.height;
          let newAngle = orig.angle;

          if (transformHandle === 'move') {
            newX = Math.max(0, Math.min(1 - orig.width, orig.x + deltaX));
            newY = Math.max(0, Math.min(1 - orig.height, orig.y + deltaY));
          } else if (transformHandle === 'br') {
            newW = Math.max(0.02, orig.width + deltaX);
            newH = Math.max(0.02, orig.height + deltaY);
          } else if (transformHandle === 'tl') {
            newX = Math.min(orig.x + orig.width - 0.02, orig.x + deltaX);
            newY = Math.min(orig.y + orig.height - 0.02, orig.y + deltaY);
            newW = orig.width - (newX - orig.x);
            newH = orig.height - (newY - orig.y);
          } else if (transformHandle === 'tr') {
            newY = Math.min(orig.y + orig.height - 0.02, orig.y + deltaY);
            newW = Math.max(0.02, orig.width + deltaX);
            newH = orig.height - (newY - orig.y);
          } else if (transformHandle === 'bl') {
            newX = Math.min(orig.x + orig.width - 0.02, orig.x + deltaX);
            newW = orig.width - (newX - orig.x);
            newH = Math.max(0.02, orig.height + deltaY);
          } else if (transformHandle === 'rotate') {
            const centerX = orig.x + orig.width / 2;
            const centerY = orig.y + orig.height / 2;
            const rad = Math.atan2(ny - centerY, nx - centerX);
            newAngle = Math.round((rad * 180) / Math.PI + 90) % 360;
          }

          const polygon = [
            [newX, newY],
            [newX + newW, newY],
            [newX + newW, newY + newH],
            [newX, newY + newH]
          ];

          return {
            ...r,
            x: newX,
            y: newY,
            width: newW,
            height: newH,
            angle: newAngle,
            polygon
          };
        })
      );
      return;
    }

    // Drawing new box
    if (isDrawing && dragStart) {
      const x1 = Math.min(dragStart.nx, nx);
      const y1 = Math.min(dragStart.ny, ny);
      const x2 = Math.max(dragStart.nx, nx);
      const y2 = Math.max(dragStart.ny, ny);
      setDraftRect({ x: x1, y: y1, w: x2 - x1, h: y2 - y1 });
    }
  };

  const handleMouseUp = () => {
    if (isPanning) {
      setIsPanning(false);
      return;
    }

    if (isTransforming) {
      setIsTransforming(false);
      setTransformHandle(null);
      setTransformStart(null);
      return;
    }

    if (isDrawing && draftRect) {
      // Minimum size: 2% width & height
      if (draftRect.w > 0.02 && draftRect.h > 0.02) {
        const poly = [
          [draftRect.x, draftRect.y],
          [draftRect.x + draftRect.w, draftRect.y],
          [draftRect.x + draftRect.w, draftRect.y + draftRect.h],
          [draftRect.x, draftRect.y + draftRect.h]
        ];

        const newRegion: AnnotationRegion = {
          id: `reg_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
          item_name: selectedItemName || 'COMPONENT',
          part_uid: selectedDrawingNo || selectedItemName,
          drawing_no: selectedDrawingNo,
          color: getLabelColor(activeLabelIndex),
          x: draftRect.x,
          y: draftRect.y,
          width: draftRect.w,
          height: draftRect.h,
          angle: 0,
          polygon: poly,
          is_visible: true
        };

        const updated = [...regions, newRegion];
        setRegions(updated);
        setSelectedRegionId(newRegion.id);

        // Keep image queue updated with regions
        if (imageQueue[currentImageIndex]) {
          imageQueue[currentImageIndex].regions = updated;
        }

        setNotification({
          type: 'success',
          message: `Created box for "${newRegion.item_name}" (${Math.round(draftRect.w * 100)}% × ${Math.round(draftRect.h * 100)}%)`
        });
      }

      setIsDrawing(false);
      setDragStart(null);
      setDraftRect(null);
    }
  };

  // 6. Draw Canvas with High-Precision Oriented Boxes, Corner Handles & Tags
  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas || !imageObjRef.current) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = imageObjRef.current.width;
    canvas.height = imageObjRef.current.height;

    // A. Draw pristine background image
    ctx.drawImage(imageObjRef.current, 0, 0);

    // B. Draw All Regions
    regions.forEach((r) => {
      if (!r.is_visible) return;
      const isSelected = r.id === selectedRegionId;
      const color = r.color || '#107C10';

      const px = r.x * canvas.width;
      const py = r.y * canvas.height;
      const pw = r.width * canvas.width;
      const ph = r.height * canvas.height;

      ctx.save();

      // Handle OBB Angle Rotation
      if (r.angle !== 0) {
        const cx = px + pw / 2;
        const cy = py + ph / 2;
        ctx.translate(cx, cy);
        ctx.rotate((r.angle * Math.PI) / 180);
        ctx.translate(-cx, -cy);
      }

      // Box Boundary Stroke
      ctx.beginPath();
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.strokeStyle = isSelected ? '#FFFFFF' : color;
      ctx.strokeRect(px, py, pw, ph);

      // Inner stroke for high contrast on bright/dark backgrounds
      ctx.lineWidth = 1;
      ctx.strokeStyle = color;
      ctx.strokeRect(px, py, pw, ph);

      // Translucent Fill
      ctx.fillStyle = isSelected ? `${color}40` : `${color}20`; // 25% or 12% opacity
      ctx.fillRect(px, py, pw, ph);

      // Top-Left Label Badge (Label Studio Tag Style)
      const labelText = r.item_name ? r.item_name.slice(0, 32) : 'UNTITLED';
      ctx.font = 'bold 11px sans-serif';
      const textWidth = ctx.measureText(labelText).width;

      ctx.fillStyle = color;
      ctx.fillRect(px, Math.max(0, py - 22), textWidth + 16, 22);

      ctx.fillStyle = '#FFFFFF';
      ctx.fillText(labelText, px + 8, Math.max(15, py - 6));

      // Draw Corner Transform Handles if Selected
      if (isSelected) {
        const handleSize = 8;
        const half = handleSize / 2;

        const handles = [
          [px, py],
          [px + pw, py],
          [px + pw, py + ph],
          [px, py + ph],
          [px + pw / 2, py],
          [px + pw / 2, py + ph],
          [px, py + ph / 2],
          [px + pw, py + ph / 2]
        ];

        handles.forEach(([hx, hy]) => {
          ctx.fillStyle = '#FFFFFF';
          ctx.fillRect(hx - half, hy - half, handleSize, handleSize);
          ctx.strokeStyle = color;
          ctx.lineWidth = 1.5;
          ctx.strokeRect(hx - half, hy - half, handleSize, handleSize);
        });

        // Rotation Handle (Stem & Circle)
        const rotX = px + pw / 2;
        const rotY = py - 26;
        ctx.beginPath();
        ctx.moveTo(px + pw / 2, py);
        ctx.lineTo(rotX, rotY);
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(rotX, rotY, 5, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();
      }

      ctx.restore();
    });

    // C. Draw Live Click & Drag Draft Box
    if (draftRect && draftRect.w > 0 && draftRect.h > 0) {
      const dpx = draftRect.x * canvas.width;
      const dpy = draftRect.y * canvas.height;
      const dpw = draftRect.w * canvas.width;
      const dph = draftRect.h * canvas.height;

      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      ctx.strokeStyle = '#00E5FF'; // Vibrant Cyan
      ctx.strokeRect(dpx, dpy, dpw, dph);
      ctx.setLineDash([]);

      ctx.fillStyle = 'rgba(0, 229, 255, 0.18)';
      ctx.fillRect(dpx, dpy, dpw, dph);

      // Dimension Pill
      ctx.fillStyle = '#004B50';
      ctx.fillRect(dpx, Math.max(0, dpy - 18), 110, 18);
      ctx.fillStyle = '#00E5FF';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(`${Math.round(dpw)} × ${Math.round(dph)} px`, dpx + 6, Math.max(13, dpy - 5));
    }
  };

  // 7. Save Annotations to YOLO Training Folder
  const handleSaveToTraining = async () => {
    if (!currentImage) {
      setNotification({ type: 'error', message: 'No component image loaded to save.' });
      return;
    }
    if (regions.length === 0) {
      setNotification({ type: 'error', message: 'Please draw at least one bounding box on the image first.' });
      return;
    }

    setIsProcessing(true);
    setNotification(null);

    try {
      const res = await api.saveComponent({
        image_base64: currentImage.base64,
        master_item_code: activeMasterCode,
        regions: regions.map((r) => ({
          item_name: r.item_name,
          part_uid: r.drawing_no || r.part_uid || r.item_name,
          drawing_no: r.drawing_no,
          polygon: r.polygon
        }))
      });

      setNotification({
        type: 'success',
        message: `Saved image '${currentImage.name}' with ${regions.length} labeled box(es) into YOLO training folder!`
      });

      // Update Summary & Parts Catalog
      const [newSummary, partsList] = await Promise.all([
        api.getDatasetSummary(),
        api.listParts()
      ]);
      setDatasetSummary(newSummary);
      setParts(partsList);

      // Auto-advance to next image in queue if available
      if (currentImageIndex < imageQueue.length - 1) {
        setCurrentImageIndex((prev) => prev + 1);
      }
    } catch (e: any) {
      setNotification({ type: 'error', message: 'Error saving component: ' + e.message });
    } finally {
      setIsProcessing(false);
    }
  };

  // 8. Auto-Detect Fastener Contours (OpenCV on Demand)
  const handleAutoContours = async () => {
    if (!currentImage) return;
    setIsProcessing(true);
    setNotification(null);
    try {
      const data = await api.autoAnnotate(60, 5, 200, 50000, currentImage.base64);
      const newRegions: AnnotationRegion[] = (data.proposals || []).map((b: any, idx: number) => {
        const poly = b.polygon || [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]];
        const xs = poly.map((p: number[]) => p[0]);
        const ys = poly.map((p: number[]) => p[1]);
        const minX = Math.min(...xs);
        const minY = Math.min(...ys);
        const maxX = Math.max(...xs);
        const maxY = Math.max(...ys);
        return {
          id: `reg_auto_${Date.now()}_${idx}`,
          item_name: selectedItemName || 'COMPONENT',
          part_uid: selectedDrawingNo || selectedItemName,
          drawing_no: selectedDrawingNo,
          color: getLabelColor(activeLabelIndex),
          x: minX,
          y: minY,
          width: maxX - minX,
          height: maxY - minY,
          angle: b.angle || 0,
          polygon: poly,
          is_visible: true
        };
      });

      if (newRegions.length > 0) {
        setRegions((prev) => [...prev, ...newRegions]);
        setNotification({ type: 'success', message: `OpenCV detected and added ${newRegions.length} component proposal(s).` });
      } else {
        setNotification({ type: 'info', message: 'No component contours found. Use BBox tool (R) to draw boxes manually.' });
      }
    } catch (e: any) {
      setNotification({ type: 'error', message: 'Auto-contour failed: ' + e.message });
    } finally {
      setIsProcessing(false);
    }
  };

  // 9. Full Image Box
  const handleSetFullImageBox = () => {
    if (!currentImage) return;
    const fullRegion: AnnotationRegion = {
      id: `reg_full_${Date.now()}`,
      item_name: selectedItemName || 'COMPONENT',
      part_uid: selectedDrawingNo || selectedItemName,
      drawing_no: selectedDrawingNo,
      color: getLabelColor(activeLabelIndex),
      x: 0.05,
      y: 0.05,
      width: 0.9,
      height: 0.9,
      angle: 0,
      polygon: [[0.05, 0.05], [0.95, 0.05], [0.95, 0.95], [0.05, 0.95]],
      is_visible: true
    };
    setRegions([fullRegion]);
    setSelectedRegionId(fullRegion.id);
  };

  // 10. Delete Selected Region
  const handleDeleteSelected = () => {
    if (!selectedRegionId) return;
    setRegions((prev) => prev.filter((r) => r.id !== selectedRegionId));
    setSelectedRegionId(null);
  };

  // 11. Clear All Regions
  const handleClearAll = () => {
    setRegions([]);
    setSelectedRegionId(null);
  };

  // 12. Trigger YOLO26 Model Training
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

  // Expose imperative actions to RibbonToolbar
  useImperativeHandle(ref, () => ({
    captureFrame: handleCaptureCamera,
    autoAnnotate: handleAutoContours,
    saveAnnotations: handleSaveToTraining,
  }));

  // Keyboard Shortcuts (Label Studio Style: R, V, Delete, Ctrl+Enter)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input
      if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') return;

      if (e.key === 'r' || e.key === 'R') {
        setActiveTool('rect');
      } else if (e.key === 'v' || e.key === 'V') {
        setActiveTool('select');
      } else if (e.key === 'h' || e.key === 'H') {
        setActiveTool('pan');
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedRegionId) {
          handleDeleteSelected();
        }
      } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        handleSaveToTraining();
      } else if (e.key >= '1' && e.key <= '9') {
        const idx = parseInt(e.key, 10) - 1;
        if (idx < availableItems.length) {
          handleSelectLabel(availableItems[idx], idx);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedRegionId, regions, currentImage, availableItems, activeLabelIndex]);

  const isTraining = trainingStatus?.status === 'RUNNING';
  const progressPct = trainingStatus && trainingStatus.total_epochs > 0
    ? (trainingStatus.current_epoch / trainingStatus.total_epochs) * 100
    : 0;

  return (
    <div className="flex-1 bg-[#F3F2F1] flex flex-col overflow-hidden text-xs select-none">
      {/* 1. TOP RIBBON TOOLBAR: Action Controls & Training Launch */}
      <div className="bg-white border-b border-[#D2D0CE] px-3 py-1.5 flex items-center justify-between shadow-sm flex-shrink-0">
        <div className="flex items-center space-x-2">
          {/* Hidden File Input */}
          <input
            type="file"
            accept="image/*"
            multiple
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
          />

          {/* Browse Images Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isProcessing || isTraining}
            className="px-3 py-1.5 bg-[#107C41] hover:bg-[#0E6032] text-white rounded font-bold flex items-center space-x-1.5 shadow transition"
            title="Select single or multiple component image files from your computer"
          >
            <FolderOpen className="w-4 h-4 text-yellow-300" />
            <span>Browse Component Images</span>
          </button>

          {/* Camera Capture */}
          <button
            onClick={handleCaptureCamera}
            disabled={isProcessing || isTraining}
            className="px-3 py-1.5 bg-[#2B579A] hover:bg-[#1E3E6D] text-white rounded font-semibold flex items-center space-x-1.5"
            title="Capture raw snapshot from conveyor camera"
          >
            <Camera className="w-4 h-4 text-white" />
            <span>Capture Frame</span>
          </button>

          <div className="h-6 w-px bg-gray-300 mx-1" />

          {/* TOOL SELECTOR GROUP (Label Studio Toolbar) */}
          <div className="flex items-center bg-gray-100 p-0.5 rounded border border-gray-300 space-x-0.5">
            <button
              onClick={() => setActiveTool('rect')}
              className={`px-2.5 py-1 rounded font-bold flex items-center space-x-1 transition ${
                activeTool === 'rect' ? 'bg-[#2B579A] text-white shadow-sm' : 'text-gray-700 hover:bg-gray-200'
              }`}
              title="Rectangle Box Tool (Shortcut: R) - Click & drag on image to draw bounding box"
            >
              <Square className="w-3.5 h-3.5" />
              <span>BBox [R]</span>
            </button>

            <button
              onClick={() => setActiveTool('select')}
              className={`px-2.5 py-1 rounded font-bold flex items-center space-x-1 transition ${
                activeTool === 'select' ? 'bg-[#2B579A] text-white shadow-sm' : 'text-gray-700 hover:bg-gray-200'
              }`}
              title="Select & Transform Tool (Shortcut: V) - Move, resize, or rotate existing boxes"
            >
              <MousePointer className="w-3.5 h-3.5" />
              <span>Select [V]</span>
            </button>

            <button
              onClick={() => setActiveTool('pan')}
              className={`px-2 py-1 rounded font-bold flex items-center space-x-1 transition ${
                activeTool === 'pan' ? 'bg-[#2B579A] text-white shadow-sm' : 'text-gray-700 hover:bg-gray-200'
              }`}
              title="Pan Tool (Shortcut: H) - Drag to navigate zoomed image"
            >
              <Move className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="h-6 w-px bg-gray-300 mx-1" />

          {/* AUTO-BOX & SHORTCUT ACTIONS */}
          <button
            onClick={handleAutoContours}
            disabled={!currentImage || isProcessing || isTraining}
            className="px-2.5 py-1 bg-white hover:bg-purple-50 border border-purple-300 text-purple-900 rounded font-semibold flex items-center space-x-1 shadow-sm disabled:opacity-40"
            title="Auto-detect component bounding boxes using OpenCV contours"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>Auto Box</span>
          </button>

          <button
            onClick={handleSetFullImageBox}
            disabled={!currentImage || isProcessing || isTraining}
            className="px-2 py-1 text-gray-700 hover:bg-gray-200 rounded font-medium border border-gray-300 disabled:opacity-40"
            title="Fit box to entire component photo"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleClearAll}
            disabled={!currentImage || regions.length === 0 || isProcessing || isTraining}
            className="px-2 py-1 text-red-600 hover:bg-red-50 rounded font-medium border border-red-200 disabled:opacity-40"
            title="Clear all drawn boxes on this image"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <div className="h-6 w-px bg-gray-300 mx-1" />

          {/* SAVE & ADD TO TRAINING FOLDER */}
          <button
            onClick={handleSaveToTraining}
            disabled={!currentImage || regions.length === 0 || isProcessing || isTraining}
            className="px-4 py-1.5 bg-[#107C10] hover:bg-[#0E6A0E] text-white rounded font-bold flex items-center space-x-1.5 shadow disabled:opacity-50"
            title="Store labeled image and annotation coordinates in training folder (Shortcut: Ctrl + Enter)"
          >
            <Save className="w-4 h-4 text-white" />
            <span>Save to Training [Ctrl+Enter]</span>
          </button>

          {/* Feedback Notification Banner */}
          {notification && (
            <div
              className={`flex items-center space-x-1.5 px-3 py-1 rounded border font-semibold ${
                notification.type === 'success'
                  ? 'bg-green-50 text-[#107C10] border-green-300'
                  : notification.type === 'info'
                  ? 'bg-blue-50 text-[#0078D4] border-blue-300'
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

        {/* Start YOLO26 Model Training Button */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleStartTraining}
            disabled={isTraining || isStartingTraining}
            className={`px-4 py-1.5 rounded font-extrabold text-white flex items-center space-x-1.5 shadow transition ${
              isTraining
                ? 'bg-amber-600 animate-pulse cursor-not-allowed'
                : 'bg-[#2B579A] hover:bg-[#1E3E6D]'
            }`}
            title="Train YOLO26-OBB model using all labeled component images in training folder"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>{isTraining ? 'Training Model...' : 'Start YOLO26 Training'}</span>
          </button>
        </div>
      </div>

      {/* 2. LABEL STUDIO COLOR-CODED QUICK LABEL PALETTE BAR */}
      <div className="bg-gray-100 border-b border-gray-300 px-3 py-1.5 flex items-center space-x-2 overflow-x-auto flex-shrink-0">
        <span className="text-[10px] uppercase font-extrabold text-gray-500 flex items-center space-x-1 flex-shrink-0">
          <Tag className="w-3 h-3 text-[#2B579A]" />
          <span>BOM Labels:</span>
        </span>

        <div className="flex items-center space-x-1.5 flex-1 overflow-x-auto py-0.5">
          {availableItems.map((it, idx) => {
            const isSelected = selectedItemName === it.item_name;
            const color = getLabelColor(idx);
            const collectedCount = datasetSummary?.parts_summary.find((p) => p.item_name === it.item_name)?.sample_count || 0;

            return (
              <button
                key={it.item_name}
                type="button"
                onClick={() => handleSelectLabel(it, idx)}
                style={{
                  backgroundColor: isSelected ? color : '#FFFFFF',
                  borderColor: color,
                  color: isSelected ? '#FFFFFF' : '#1A1A1A'
                }}
                className={`px-2.5 py-1 rounded text-xs font-bold border flex items-center space-x-1.5 transition-all shadow-sm flex-shrink-0 ${
                  isSelected ? 'ring-2 ring-offset-1 ring-blue-500 scale-105' : 'hover:bg-gray-50'
                }`}
                title={`[${idx + 1}] ${it.item_name} - ${collectedCount} sample(s) collected`}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0 border border-white/60"
                  style={{ backgroundColor: isSelected ? '#FFFFFF' : color }}
                />
                <span className="font-mono text-[10px] opacity-75">#{idx + 1}</span>
                <span className="truncate max-w-[180px]">{it.item_name}</span>
                <span
                  className={`text-[10px] px-1 rounded font-mono ${
                    isSelected ? 'bg-black/25 text-white' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {collectedCount}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. MAIN WORKSPACE SPLIT: Viewport Canvas (70%) + Label Studio Inspector Panel (30%) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Annotation Canvas Viewport */}
        <div
          ref={viewportContainerRef}
          className="flex-1 bg-[#1E1E1E] flex flex-col relative overflow-hidden select-none"
        >
          {/* Canvas Floating Top Controls: Zoom, Pan, Fit */}
          <div className="absolute top-3 left-3 z-20 flex items-center space-x-1 bg-black/75 backdrop-blur-sm p-1 rounded border border-gray-700 shadow-md">
            <button
              onClick={() => setZoom((z) => Math.min(6.0, parseFloat((z + 0.25).toFixed(2))))}
              className="p-1 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Zoom In (or Scroll Wheel Up)"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <span className="text-[11px] font-mono text-yellow-300 px-1 font-bold">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.max(0.25, parseFloat((z - 0.25).toFixed(2))))}
              className="p-1 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Zoom Out (or Scroll Wheel Down)"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={resetZoomAndPan}
              className="px-2 py-0.5 text-[11px] font-semibold text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Fit entire image to screen"
            >
              Fit
            </button>
          </div>

          {/* Interactive Canvas Area */}
          <div
            onWheel={handleWheel}
            className="flex-1 flex items-center justify-center p-4 relative overflow-hidden"
          >
            {currentImage ? (
              <div
                style={{
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                  transformOrigin: 'center center',
                  transition: isPanning ? 'none' : 'transform 0.05s ease-out'
                }}
                className={`relative flex items-center justify-center shadow-2xl ${
                  activeTool === 'rect' || activeTool === 'obb'
                    ? 'cursor-crosshair'
                    : activeTool === 'pan'
                    ? isPanning ? 'cursor-grabbing' : 'cursor-grab'
                    : 'cursor-default'
                }`}
              >
                <canvas
                  ref={canvasRef}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                  style={{
                    width: `${canvasDisplaySize.width}px`,
                    height: `${canvasDisplaySize.height}px`,
                  }}
                  className="rounded border border-gray-600 bg-black block shadow-2xl"
                />
              </div>
            ) : (
              <div className="text-center text-gray-400 p-8 space-y-3">
                <ImageIcon className="w-16 h-16 mx-auto text-gray-600" />
                <p className="text-sm font-semibold">No Component Image in Queue</p>
                <p className="text-xs text-gray-500 max-w-md mx-auto">
                  Click <strong>"Browse Component Images"</strong> to load single or multiple photos from disk, or grab a frame directly from your <strong>Camera</strong>.
                </p>
              </div>
            )}
          </div>

          {/* Bottom Filmstrip / Image Queue Navigator (Label Studio Pagination) */}
          {imageQueue.length > 0 && (
            <div className="h-16 bg-[#252526] border-t border-gray-700 px-3 py-1 flex items-center justify-between flex-shrink-0 z-20">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentImageIndex((i) => Math.max(0, i - 1))}
                  disabled={currentImageIndex === 0}
                  className="p-1 rounded bg-gray-800 hover:bg-gray-700 text-white disabled:opacity-30"
                  title="Previous Image (Shortcut: A)"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-xs font-mono text-gray-300 font-bold">
                  {currentImageIndex + 1} / {imageQueue.length}
                </span>
                <button
                  onClick={() => setCurrentImageIndex((i) => Math.min(imageQueue.length - 1, i + 1))}
                  disabled={currentImageIndex === imageQueue.length - 1}
                  className="p-1 rounded bg-gray-800 hover:bg-gray-700 text-white disabled:opacity-30"
                  title="Next Image (Shortcut: D)"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>

              {/* Thumbnail Strip */}
              <div className="flex items-center space-x-2 overflow-x-auto px-2">
                {imageQueue.map((item, idx) => (
                  <button
                    key={item.id}
                    onClick={() => setCurrentImageIndex(idx)}
                    className={`relative rounded border-2 overflow-hidden w-16 h-12 flex-shrink-0 transition-all ${
                      idx === currentImageIndex ? 'border-[#0078D4] ring-2 ring-white scale-105' : 'border-gray-600 opacity-60 hover:opacity-100'
                    }`}
                  >
                    <img src={item.base64} alt={item.name} className="w-full h-full object-cover" />
                    {item.regions.length > 0 && (
                      <span className="absolute bottom-0 right-0 bg-[#107C10] text-white text-[9px] font-bold px-1 rounded-tl">
                        {item.regions.length}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              <div className="text-[11px] text-gray-400 font-mono">
                {currentImage?.name}
              </div>
            </div>
          )}
        </div>

        {/* Right: Label Studio Region Inspector & Training Folder Manager */}
        <div className="w-[380px] bg-white border-l border-[#D2D0CE] flex flex-col h-full overflow-hidden flex-shrink-0">
          {/* Header */}
          <div className="p-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-gray-800 text-xs uppercase tracking-wider flex items-center space-x-1.5">
                <Layers className="w-4 h-4 text-[#2B579A]" />
                <span>Regions & Annotations</span>
              </h3>
              <p className="text-[11px] text-gray-500">
                {regions.length} box(es) drawn on current image
              </p>
            </div>

            {selectedRegionId && (
              <button
                onClick={handleDeleteSelected}
                className="p-1 text-red-600 hover:bg-red-50 rounded"
                title="Delete Selected Box (Shortcut: Delete)"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Region List (Label Studio Region Sidebar) */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5 border-b border-gray-200">
            {regions.length === 0 ? (
              <div className="p-6 text-center text-gray-400">
                <Crosshair className="w-8 h-8 mx-auto text-gray-300 mb-2" />
                <p className="font-semibold text-xs">No boxes drawn yet</p>
                <p className="text-[11px] text-gray-500 mt-1">
                  Click and drag on the image to outline a component, or click <strong>Auto Box</strong>.
                </p>
              </div>
            ) : (
              regions.map((reg, idx) => {
                const isSelected = reg.id === selectedRegionId;
                return (
                  <div
                    key={reg.id}
                    onClick={() => setSelectedRegionId(reg.id)}
                    style={{ borderLeftColor: reg.color }}
                    className={`p-2 rounded border border-l-4 transition-all cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? 'bg-blue-50/80 border-blue-400 shadow-sm'
                        : 'bg-white hover:bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2 flex-1 min-w-0 pr-2">
                      <span
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: reg.color }}
                      />
                      <div className="min-w-0">
                        <span className="font-bold text-xs text-gray-900 block truncate">
                          #{idx + 1} {reg.item_name}
                        </span>
                        <span className="text-[10px] text-gray-500 font-mono">
                          {Math.round(reg.width * 100)}% × {Math.round(reg.height * 100)}% {reg.angle ? `(${reg.angle}°)` : ''}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setRegions((prev) =>
                            prev.map((r) => (r.id === reg.id ? { ...r, is_visible: !r.is_visible } : r))
                          );
                        }}
                        className="p-1 text-gray-400 hover:text-gray-700"
                        title={reg.is_visible ? 'Hide Box' : 'Show Box'}
                      >
                        {reg.is_visible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5 text-gray-400" />}
                      </button>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setRegions((prev) => prev.filter((r) => r.id !== reg.id));
                          if (selectedRegionId === reg.id) setSelectedRegionId(null);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Delete this box"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Dataset Status & Training Folder Breakdown */}
          <div className="p-3 bg-gray-50 border-t border-gray-200 flex-shrink-0">
            <div className="flex justify-between items-center mb-1.5">
              <span className="font-bold text-xs uppercase text-gray-700">Dataset Status</span>
              <span className="text-xs font-mono font-bold text-[#107C10]">
                {datasetSummary?.total_images || 0} images in dataset
              </span>
            </div>

            {/* Quick Instruction Banner */}
            <div className="bg-white p-2 rounded border border-gray-300 text-[11px] text-gray-600 space-y-1">
              <div className="flex items-center space-x-1 font-semibold text-gray-800">
                <HelpCircle className="w-3.5 h-3.5 text-[#2B579A]" />
                <span>Label Studio Shortcuts:</span>
              </div>
              <p>• <strong>R</strong>: Box tool | <strong>V</strong>: Select tool</p>
              <p>• <strong>1–9</strong>: Quick select BOM label</p>
              <p>• <strong>Delete</strong>: Remove selected box</p>
              <p>• <strong>Ctrl + Enter</strong>: Save & Next Image</p>
            </div>
          </div>
        </div>
      </div>

      {/* 4. BOTTOM TRAINING CONSOLE DRAWER (Shows when training is active) */}
      {showTrainingPanel && (
        <div className="h-56 bg-[#1E1E1E] border-t-2 border-[#2B579A] text-white flex flex-col flex-shrink-0 shadow-2xl">
          <div className="bg-[#252526] px-4 py-1.5 flex items-center justify-between border-b border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Cpu className={`w-4 h-4 ${isTraining ? 'text-amber-400 animate-spin' : 'text-green-400'}`} />
                <span className="font-bold uppercase tracking-wider text-xs">
                  YOLO26-OBB Training Progress: {trainingStatus?.status || 'IDLE'}
                </span>
              </div>
              {trainingStatus && trainingStatus.total_epochs > 0 && (
                <span className="text-xs font-mono text-yellow-300">
                  Epoch {trainingStatus.current_epoch} / {trainingStatus.total_epochs} ({Math.round(progressPct)}%)
                </span>
              )}
            </div>

            <button
              onClick={() => setShowTrainingPanel(false)}
              className="text-gray-400 hover:text-white text-xs px-2 py-0.5"
            >
              Minimize ✕
            </button>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-800 h-1.5">
            <div
              className={`h-full transition-all duration-300 ${
                trainingStatus?.status === 'COMPLETED' ? 'bg-green-500' : 'bg-[#0078D4]'
              }`}
              style={{ width: `${progressPct}%` }}
            />
          </div>

          {/* Live Console Output */}
          <div
            ref={logsContainerRef}
            className="flex-1 p-3 font-mono text-[11px] overflow-y-auto space-y-1 text-gray-300 select-text"
          >
            {trainingStatus?.logs && trainingStatus.logs.length > 0 ? (
              trainingStatus.logs.map((line, i) => (
                <div key={i} className="leading-tight">
                  {line}
                </div>
              ))
            ) : (
              <div className="text-gray-500 italic">Waiting for training logs...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
});

LabelingStudioTab.displayName = 'LabelingStudioTab';
