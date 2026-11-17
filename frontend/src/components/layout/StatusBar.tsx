import React from 'react';
import { Activity, Gauge, CheckSquare, ZoomIn, ZoomOut } from 'lucide-react';

interface StatusBarProps {
  fps: number;
  latencyMs: number;
  activeModelName: string;
  totalBatches: number;
  passCount: number;
  zoomLevel: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  fps,
  latencyMs,
  activeModelName,
  totalBatches,
  passCount,
  zoomLevel,
  onZoomIn,
  onZoomOut
}) => {
  const yieldPct = totalBatches > 0 ? ((passCount / totalBatches) * 100).toFixed(1) : "100.0";

  return (
    <div className="bg-[#2B579A] text-white h-6 px-3 flex items-center justify-between text-[11px] select-none font-mono border-t border-[#1E3E6D]">
      {/* Left: Performance Metrics */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1">
          <Activity className="w-3.5 h-3.5 text-green-300" />
          <span>FPS: <strong className="text-yellow-300">{fps.toFixed(1)}</strong></span>
        </div>

        <div className="flex items-center space-x-1">
          <Gauge className="w-3.5 h-3.5 text-cyan-300" />
          <span>Latency: <strong>{latencyMs}ms</strong></span>
        </div>

        <div className="text-blue-200">
          Model: <span className="text-white font-bold">{activeModelName}</span> (nms=False)
        </div>
      </div>

      {/* Center: Shift Yield */}
      <div className="flex items-center space-x-2">
        <CheckSquare className="w-3.5 h-3.5 text-green-300" />
        <span>Batch Yield: <strong className="text-yellow-300">{yieldPct}%</strong> ({passCount}/{totalBatches} Passed)</span>
      </div>

      {/* Right: Viewport Controls */}
      <div className="flex items-center space-x-2">
        <span>Zoom: {zoomLevel}%</span>
        <button
          onClick={onZoomOut}
          className="hover:bg-blue-800 p-0.5 rounded text-gray-200 hover:text-white"
          title="Zoom out"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onZoomIn}
          className="hover:bg-blue-800 p-0.5 rounded text-gray-200 hover:text-white"
          title="Zoom in"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
