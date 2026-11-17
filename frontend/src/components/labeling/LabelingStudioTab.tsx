import React, { useState, useEffect, useRef } from 'react';
import { Camera, Sparkles, Save, Sliders, Trash2, CheckCircle2, Filter } from 'lucide-react';
import { api } from '../../services/api';
import { PartCatalogItem } from '../../types/bom';

interface ProposalBox {
  id: string;
  polygon: number[][]; // [[x1, y1], [x2, y2], [x3, y3], [x4, y4]] normalized
  center: [number, number];
  width: number;
  height: number;
  angle: number;
  area: number;
  part_uid: string;
}

interface LabelingStudioTabProps {
  activeMasterCode: string;
}

export const LabelingStudioTab: React.FC<LabelingStudioTabProps> = ({
  activeMasterCode
}) => {
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [proposals, setProposals] = useState<ProposalBox[]>([]);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [parts, setParts] = useState<PartCatalogItem[]>([]);
  const [filterUntrained, setFilterUntrained] = useState(false);
  const [thresholdVal, setThresholdVal] = useState(60);
  const [blurKernel, setBlurKernel] = useState(5);
  const [minArea, setMinArea] = useState(300);
  const [isProcessing, setIsProcessing] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageObjRef = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    api.listParts().then(setParts).catch(console.error);
    handleCapture();
  }, []);

  const handleCapture = async () => {
    setIsProcessing(true);
    setSaveMessage(null);
    try {
      const data = await api.captureFrame();
      setImageBase64(data.image_base64);
      setProposals(data.proposals || []);

      const img = new Image();
      img.src = data.image_base64;
      img.onload = () => {
        imageObjRef.current = img;
        drawCanvas(data.proposals || []);
      };
    } catch (e: any) {
      console.error("Frame capture error:", e);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAutoAnnotate = async () => {
    setIsProcessing(true);
    try {
      const data = await api.autoAnnotate(thresholdVal, blurKernel, minArea, 50000);
      setProposals(data.proposals);
      drawCanvas(data.proposals);
    } catch (e: any) {
      console.error("Auto annotate error:", e);
    } finally {
      setIsProcessing(false);
    }
  };

  const drawCanvas = (boxes: ProposalBox[], activeId: string | null = selectedBoxId) => {
    const canvas = canvasRef.current;
    if (!canvas || !imageObjRef.current) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = imageObjRef.current.width;
    canvas.height = imageObjRef.current.height;

    // Draw base image
    ctx.drawImage(imageObjRef.current, 0, 0);

    // Draw OBB boxes
    boxes.forEach((b) => {
      const isSelected = b.id === activeId;
      ctx.beginPath();
      ctx.lineWidth = isSelected ? 4 : 2;
      ctx.strokeStyle = isSelected ? '#00E5FF' : b.part_uid ? '#107C10' : '#D13438';

      const pts = b.polygon.map(([nx, ny]) => [nx * canvas.width, ny * canvas.height]);
      if (pts.length === 4) {
        ctx.moveTo(pts[0][0], pts[0][1]);
        ctx.lineTo(pts[1][0], pts[1][1]);
        ctx.lineTo(pts[2][0], pts[2][1]);
        ctx.lineTo(pts[3][0], pts[3][1]);
        ctx.closePath();
        ctx.stroke();

        // Fill subtle translucent tint
        ctx.fillStyle = isSelected ? 'rgba(0, 229, 255, 0.2)' : 'rgba(255, 255, 255, 0.05)';
        ctx.fill();

        // Draw part label tag
        const cx = b.center[0] * canvas.width;
        const cy = b.center[1] * canvas.height;
        ctx.fillStyle = isSelected ? '#00E5FF' : '#201F1E';
        ctx.fillRect(cx - 20, cy - 12, 120, 16);
        ctx.fillStyle = isSelected ? '#000000' : '#FFFFFF';
        ctx.font = '10px monospace';
        ctx.fillText(b.part_uid ? b.part_uid.slice(0, 14) : 'UNASSIGNED', cx - 16, cy);
      }
    });
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const clickX = (e.clientX - rect.left) * scaleX;
    const clickY = (e.clientY - rect.top) * scaleY;

    // Find clicked box
    let clickedId: string | null = null;
    for (const b of proposals) {
      const cx = b.center[0] * canvas.width;
      const cy = b.center[1] * canvas.height;
      const dist = Math.hypot(clickX - cx, clickY - cy);
      if (dist < 45) {
        clickedId = b.id;
        break;
      }
    }
    setSelectedBoxId(clickedId);
    drawCanvas(proposals, clickedId);
  };

  const handleAssignPart = (partUid: string) => {
    if (!selectedBoxId) return;
    const updated = proposals.map((b) =>
      b.id === selectedBoxId ? { ...b, part_uid: partUid } : b
    );
    setProposals(updated);
    drawCanvas(updated, selectedBoxId);
  };

  const handleDeleteBox = (boxId: string) => {
    const updated = proposals.filter((b) => b.id !== boxId);
    setProposals(updated);
    setSelectedBoxId(null);
    drawCanvas(updated, null);
  };

  const handleSave = async () => {
    const validBoxes = proposals.filter((b) => b.part_uid);
    if (validBoxes.length === 0) {
      alert("Please assign a Part UID to at least one box before saving.");
      return;
    }
    setIsProcessing(true);
    try {
      const res = await api.saveAnnotations(proposals, activeMasterCode);
      setSaveMessage(`Successfully saved ${res.result.boxes_saved} OBB annotations to YOLO dataset!`);
      // Refresh parts catalog sample counts
      api.listParts().then(setParts);
    } catch (e: any) {
      alert("Error saving annotations: " + e.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const displayedParts = filterUntrained
    ? parts.filter((p) => p.training_status !== 'TRAINED')
    : parts;

  return (
    <div className="flex-1 bg-[#F3F2F1] flex flex-col overflow-hidden text-xs select-none">
      {/* Top Controls Toolbar */}
      <div className="bg-white border-b border-[#D2D0CE] px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={handleCapture}
            disabled={isProcessing}
            className="px-3 py-1.5 bg-[#2B579A] hover:bg-[#1E3E6D] text-white rounded font-semibold flex items-center space-x-1.5"
          >
            <Camera className="w-4 h-4" />
            <span>Capture Frame</span>
          </button>

          <button
            onClick={handleAutoAnnotate}
            disabled={isProcessing}
            className="px-3 py-1.5 bg-purple-700 hover:bg-purple-800 text-white rounded font-semibold flex items-center space-x-1.5"
          >
            <Sparkles className="w-4 h-4" />
            <span>Re-Segment Contours</span>
          </button>

          <button
            onClick={handleSave}
            disabled={isProcessing}
            className="px-3 py-1.5 bg-[#107C10] hover:bg-[#0E6A0E] text-white rounded font-bold flex items-center space-x-1.5 shadow"
          >
            <Save className="w-4 h-4" />
            <span>Save YOLO-OBB Labels</span>
          </button>

          {saveMessage && (
            <span className="text-[#107C10] font-bold flex items-center space-x-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>{saveMessage}</span>
            </span>
          )}
        </div>

        {/* Sliders Accordion */}
        <div className="flex items-center space-x-4 text-[11px] text-gray-700 font-mono">
          <div className="flex items-center space-x-1">
            <span>Threshold:</span>
            <input
              type="range"
              min="20"
              max="200"
              value={thresholdVal}
              onChange={(e) => setThresholdVal(parseInt(e.target.value))}
              className="w-20"
            />
            <span>{thresholdVal}</span>
          </div>

          <div className="flex items-center space-x-1">
            <span>Min Area:</span>
            <input
              type="range"
              min="100"
              max="2000"
              step="50"
              value={minArea}
              onChange={(e) => setMinArea(parseInt(e.target.value))}
              className="w-20"
            />
            <span>{minArea}</span>
          </div>
        </div>
      </div>

      {/* Main Workspace Split */}
      <div className="flex-1 flex overflow-hidden">
        {/* Canvas Area (Left) */}
        <div className="flex-1 bg-black flex items-center justify-center p-3 overflow-auto">
          {imageBase64 ? (
            <canvas
              ref={canvasRef}
              onClick={handleCanvasClick}
              className="max-h-full max-w-full object-contain cursor-crosshair border border-gray-600 rounded shadow"
            />
          ) : (
            <div className="text-gray-400 italic">No image captured. Click "Capture Frame" to begin.</div>
          )}
        </div>

        {/* Right Sidebar: Box Manager & Part Selector */}
        <div className="w-80 bg-white border-l border-[#D2D0CE] flex flex-col h-full overflow-hidden">
          <div className="p-3 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
            <span className="font-bold text-gray-800">
              Detected Boxes ({proposals.length})
            </span>
            <button
              onClick={() => setFilterUntrained(!filterUntrained)}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1 ${filterUntrained ? 'bg-yellow-200 text-yellow-900' : 'bg-gray-200 text-gray-700'}`}
            >
              <Filter className="w-3 h-3" />
              <span>Only Untrained</span>
            </button>
          </div>

          {/* Selected Box Details */}
          {selectedBoxId && (
            <div className="p-3 bg-cyan-50 border-b border-cyan-200 space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-cyan-900">Selected OBB Box</span>
                <button
                  onClick={() => handleDeleteBox(selectedBoxId)}
                  className="text-red-600 hover:text-red-800 p-1 rounded"
                  title="Delete Box"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-gray-600 block mb-1">
                  Assign Part UID (Drawing No):
                </label>
                <select
                  value={proposals.find((b) => b.id === selectedBoxId)?.part_uid || ""}
                  onChange={(e) => handleAssignPart(e.target.value)}
                  className="w-full p-1.5 border border-gray-300 rounded font-mono text-xs bg-white"
                >
                  <option value="">-- Select Hardware Part --</option>
                  {displayedParts.map((p) => (
                    <option key={p.part_uid} value={p.part_uid}>
                      {p.drawing_no !== "—" ? `[${p.drawing_no}]` : "[NO DWG]"} {p.item_name} ({p.training_status})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Box List */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {proposals.map((b, idx) => {
              const isSelected = b.id === selectedBoxId;
              return (
                <div
                  key={b.id}
                  onClick={() => {
                    setSelectedBoxId(b.id);
                    drawCanvas(proposals, b.id);
                  }}
                  className={`p-2 rounded border cursor-pointer flex items-center justify-between transition ${isSelected ? 'bg-cyan-100 border-cyan-400 font-bold' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'}`}
                >
                  <div>
                    <span className="font-mono text-xs text-gray-600">Box #{idx + 1}</span>
                    <p className="font-mono text-[11px] text-blue-700 truncate max-w-[170px]">
                      {b.part_uid || "Unassigned"}
                    </p>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${b.part_uid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {b.part_uid ? "LABELED" : "EMPTY"}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
