import React, { useRef, useState, useEffect } from 'react';
import { Sliders, CheckCircle2, AlertTriangle, Play, Camera, RefreshCw } from 'lucide-react';
import { TripwireGeometry } from '../../types/bom';

interface ConveyorViewportProps {
  streamUrl: string;
  tripwire: TripwireGeometry;
  onUpdateTripwire: (coords: [number, number, number, number]) => void;
  isTripwireEditMode: boolean;
  overallStatus: string;
  totalTarget: number;
  totalCounted: number;
  zoomLevel: number;
  cameraMode?: string;
  cameraIndex?: number;
  onSwitchCamera?: (mode: string, index?: number) => void;
  onOpenCameraSettings?: () => void;
}

export const ConveyorViewport: React.FC<ConveyorViewportProps> = ({
  streamUrl,
  tripwire,
  onUpdateTripwire,
  isTripwireEditMode,
  overallStatus,
  totalTarget,
  totalCounted,
  zoomLevel,
  cameraMode = 'USB',
  cameraIndex = 0,
  onSwitchCamera,
  onOpenCameraSettings
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [draggingHandle, setDraggingHandle] = useState<'p1' | 'p2' | null>(null);
  const [localCoords, setLocalCoords] = useState<[number, number, number, number]>(tripwire.coords);

  useEffect(() => {
    setLocalCoords(tripwire.coords);
  }, [tripwire]);

  const handleMouseDown = (handle: 'p1' | 'p2') => (e: React.MouseEvent) => {
    if (!isTripwireEditMode) return;
    e.preventDefault();
    setDraggingHandle(handle);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggingHandle || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0.02, Math.min(0.98, (e.clientX - rect.left) / rect.width));
    const y = Math.max(0.02, Math.min(0.98, (e.clientY - rect.top) / rect.height));

    const updated = [...localCoords] as [number, number, number, number];
    if (draggingHandle === 'p1') {
      updated[0] = x;
      updated[1] = y;
    } else {
      updated[2] = x;
      updated[3] = y;
    }
    setLocalCoords(updated);
  };

  const handleMouseUp = () => {
    if (draggingHandle) {
      setDraggingHandle(null);
      onUpdateTripwire(localCoords);
    }
  };

  return (
    <div
      className="relative flex-1 bg-black flex flex-col items-center justify-between overflow-hidden border-r border-[#D2D0CE] select-none"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* 1. TOP DEDICATED CAMERA SOURCE & DEVICE INDEX SELECTOR BAR */}
      <div className="w-full bg-[#1E3E6D] text-white px-3 py-1.5 flex items-center justify-between border-b-2 border-[#2B579A] text-xs z-30 shadow-md flex-shrink-0">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 font-bold text-yellow-300">
            <Camera className="w-4 h-4 text-green-400" />
            <span className="uppercase tracking-wider">LIVE CAMERA SOURCE:</span>
          </div>

          {/* Camera Source Selector Dropdown */}
          <select
            value={`USB_${cameraIndex}`}
            onChange={(e) => {
              const val = e.target.value;
              if (val === 'SETTINGS') {
                onOpenCameraSettings && onOpenCameraSettings();
              } else if (val.startsWith('USB_')) {
                onSwitchCamera && onSwitchCamera('USB', parseInt(val.split('_')[1], 10));
              }
            }}
            className="bg-white text-gray-900 font-bold px-2.5 py-1 rounded text-xs border-2 border-yellow-400 focus:outline-none focus:ring-2 focus:ring-yellow-300 cursor-pointer shadow"
          >
            <option value="USB_0">📹 USB Camera [Index 0]</option>
            <option value="USB_1">📹 USB Camera [Index 1]</option>
            <option value="USB_2">📹 USB Camera [Index 2]</option>
            <option value="USB_3">📹 USB Camera [Index 3]</option>
            <option value="SETTINGS">⚙️ Camera Settings & Port Scan...</option>
          </select>

          {/* Direct 1-Click Camera Index Buttons */}
          <div className="flex items-center space-x-1 bg-black/40 px-2 py-0.5 rounded border border-blue-400/30">
            <span className="text-[11px] text-blue-200 font-bold uppercase mr-1">Choose Index:</span>
            {[0, 1, 2, 3, 4].map((idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSwitchCamera && onSwitchCamera('USB', idx)}
                className={`w-6 h-5 rounded text-xs font-mono font-bold transition-all ${
                  cameraMode === 'USB' && cameraIndex === idx
                    ? 'bg-yellow-400 text-black shadow-md ring-2 ring-white scale-105'
                    : 'bg-[#2B579A] hover:bg-blue-600 text-white'
                }`}
                title={`Click to connect directly to USB Camera Index ${idx}`}
              >
                {idx}
              </button>
            ))}
          </div>
        </div>

        {/* Right: Camera Settings Button & Real-Time Indicator */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={onOpenCameraSettings}
            className="flex items-center space-x-1.5 bg-[#107C41] hover:bg-[#0E6032] text-white px-2.5 py-1 rounded text-xs font-bold border border-green-300/40 transition-colors shadow-sm"
            title="Open Camera Hardware Settings Modal"
          >
            <Sliders className="w-3.5 h-3.5 text-yellow-300" />
            <span>Camera Setup</span>
          </button>

          <div className="flex items-center space-x-1.5 bg-black/60 px-2.5 py-1 rounded text-[11px] font-mono text-green-300 border border-green-500/30">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
            <span className="font-bold">
              ACTIVE: USB CAM [{cameraIndex}]
            </span>
          </div>
        </div>
      </div>

      {/* 2. Top Floating Inspection Status Banner */}
      <div className="w-full px-3 pt-2 z-20 pointer-events-none">
        {overallStatus === 'PASS' ? (
          <div className="bg-[#107C10] text-white px-4 py-1.5 rounded shadow-lg flex items-center space-x-2 border-2 border-white/50 w-full justify-center animate-pulse pointer-events-auto">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-extrabold text-sm uppercase tracking-wider">
              PASS - 100% BOM MATCH ({totalCounted}/{totalTarget} PCS VERIFIED)
            </span>
          </div>
        ) : (
          <div className="bg-[#2B579A]/95 text-white px-4 py-1.5 rounded shadow-md flex items-center space-x-2 border border-blue-400/40 w-full justify-between pointer-events-auto">
            <div className="flex items-center space-x-2">
              <Play className="w-4 h-4 text-green-400 fill-green-400" />
              <span className="font-bold text-xs uppercase tracking-wide">
                CONVEYOR INSPECTING: BATCH IN PROGRESS
              </span>
            </div>
            <div className="font-mono font-bold text-sm text-yellow-300">
              {totalCounted} / {totalTarget} PCS
            </div>
          </div>
        )}
      </div>

      {/* 3. Main Video Viewport Canvas Container */}
      <div
        ref={containerRef}
        className="relative w-full flex-1 flex items-center justify-center overflow-hidden"
        style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'center center' }}
      >
        <img
          src={streamUrl}
          alt="Conveyor Video Stream"
          className="w-full h-full object-contain pointer-events-none"
        />

        {/* Interactive Tripwire SVG Overlay when in edit mode */}
        {isTripwireEditMode && containerRef.current && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
            <line
              x1={`${localCoords[0] * 100}%`}
              y1={`${localCoords[1] * 100}%`}
              x2={`${localCoords[2] * 100}%`}
              y2={`${localCoords[3] * 100}%`}
              stroke="#00E5FF"
              strokeWidth="4"
              strokeDasharray="8 4"
            />
          </svg>
        )}

        {/* Grab Handles for Tripwire */}
        {isTripwireEditMode && (
          <>
            <div
              style={{ left: `${localCoords[0] * 100}%`, top: `${localCoords[1] * 100}%` }}
              onMouseDown={handleMouseDown('p1')}
              className="absolute -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-yellow-400 border-2 border-black rounded-full cursor-grab active:cursor-grabbing z-30 shadow-lg flex items-center justify-center text-[10px] font-bold"
              title="Drag Tripwire Start Point"
            >
              P1
            </div>

            <div
              style={{ left: `${localCoords[2] * 100}%`, top: `${localCoords[3] * 100}%` }}
              onMouseDown={handleMouseDown('p2')}
              className="absolute -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-yellow-400 border-2 border-black rounded-full cursor-grab active:cursor-grabbing z-30 shadow-lg flex items-center justify-center text-[10px] font-bold"
              title="Drag Tripwire End Point"
            >
              P2
            </div>
          </>
        )}
      </div>

      {/* Direction & Edit Mode Notice */}
      {isTripwireEditMode && (
        <div className="absolute bottom-2 left-3 bg-black/80 text-yellow-300 text-xs px-3 py-1 rounded border border-yellow-400 z-20 flex items-center space-x-2">
          <Sliders className="w-4 h-4" />
          <span>Tripwire Calibration Active: Drag yellow P1/P2 handles to position line across belt.</span>
        </div>
      )}
    </div>
  );
};
