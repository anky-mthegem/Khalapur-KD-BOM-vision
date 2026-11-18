import React, { useState, useEffect } from 'react';
import {
  Camera,
  RefreshCw,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  X,
  Check
} from 'lucide-react';
import { api } from '../../services/api';
import { CameraDevice, CameraStatus } from '../../types/bom';

interface CameraSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSourceChanged: (status: CameraStatus) => void;
  currentStatus: CameraStatus | null;
}

export const CameraSettingsModal: React.FC<CameraSettingsModalProps> = ({
  isOpen,
  onClose,
  onSourceChanged,
  currentStatus
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [resolution, setResolution] = useState<{ width: number; height: number }>({ width: 1280, height: 720 });
  const [devices, setDevices] = useState<CameraDevice[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    if (isOpen) {
      if (currentStatus) {
        setSelectedIndex(currentStatus.device_index ?? 0);
      }
      loadDevices(false);
    }
  }, [isOpen, currentStatus]);

  const loadDevices = async (force: boolean = false) => {
    setIsScanning(true);
    setNotification(null);
    try {
      const res = await api.getCameraDevices(force);
      setDevices(res.devices || []);
      if (res.current_index !== undefined) {
        setSelectedIndex(res.current_index);
      }
    } catch (e: any) {
      console.warn("Could not probe camera devices:", e);
    } finally {
      setIsScanning(false);
    }
  };

  const handleApply = async () => {
    setIsApplying(true);
    setNotification(null);
    try {
      const res = await api.switchCameraSource({
        mode: 'USB',
        device_index: selectedIndex,
        width: resolution.width,
        height: resolution.height
      });
      setNotification({
        type: 'success',
        message: `Connected to USB Camera Index [${selectedIndex}] (${resolution.width}x${resolution.height}).`
      });
      onSourceChanged(res);
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (e: any) {
      setNotification({
        type: 'error',
        message: 'Failed to connect to USB camera: ' + e.message
      });
    } finally {
      setIsApplying(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none">
      <div className="bg-[#F3F2F1] rounded-lg shadow-2xl border-2 border-[#2B579A] w-full max-w-xl overflow-hidden flex flex-col">
        {/* Title Bar */}
        <div className="bg-[#2B579A] text-white px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Camera className="w-5 h-5 text-yellow-300" />
            <span className="font-bold text-sm tracking-wide">
              USB CAMERA HARDWARE CONFIGURATION & INDEX SELECTION
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 p-1 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          {notification && (
            <div
              className={`p-3 rounded text-xs font-semibold flex items-center space-x-2 ${
                notification.type === 'success'
                  ? 'bg-green-100 border border-green-400 text-green-900'
                  : 'bg-red-100 border border-red-400 text-red-900'
              }`}
            >
              {notification.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-green-700 flex-shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-red-700 flex-shrink-0" />
              )}
              <span>{notification.message}</span>
            </div>
          )}

          {/* USB Device Index Configuration */}
          <div className="bg-white p-4 rounded border border-gray-300 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-gray-900 uppercase tracking-wide flex items-center space-x-1.5">
                  <Camera className="w-4 h-4 text-[#2B579A]" />
                  <span>Select USB Camera Port / Index</span>
                </h3>
                <p className="text-[11px] text-gray-500 mt-0.5">
                  Choose the hardware index number for your overhead conveyor or inspection camera.
                </p>
              </div>
              <button
                type="button"
                onClick={() => loadDevices(true)}
                disabled={isScanning}
                className="flex items-center space-x-1.5 bg-gray-100 hover:bg-gray-200 text-gray-800 px-2.5 py-1 rounded border border-gray-300 text-xs font-semibold transition-colors disabled:opacity-50"
                title="Rescan USB ports on this workstation"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-gray-600 ${isScanning ? 'animate-spin' : ''}`} />
                <span>{isScanning ? 'Scanning...' : 'Rescan Ports'}</span>
              </button>
            </div>

            {/* Detected Devices List */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-gray-700">Detected USB Video Devices:</span>
              {devices.length === 0 ? (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800 flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-600 flex-shrink-0" />
                  <span>No USB cameras automatically enumerated. You can still select an index number below.</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-2">
                  {devices.map((dev) => (
                    <div
                      key={dev.index}
                      onClick={() => setSelectedIndex(dev.index)}
                      className={`px-3 py-2 rounded border flex items-center justify-between cursor-pointer transition-colors ${
                        selectedIndex === dev.index
                          ? 'bg-blue-50 border-[#2B579A] text-blue-900 font-semibold ring-1 ring-[#2B579A]'
                          : 'bg-gray-50 border-gray-200 hover:bg-white text-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5">
                        <input
                          type="radio"
                          name="cameraIndex"
                          checked={selectedIndex === dev.index}
                          onChange={() => setSelectedIndex(dev.index)}
                          className="text-[#2B579A] focus:ring-[#2B579A]"
                        />
                        <div>
                          <span className="font-mono text-xs font-bold mr-2 bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
                            Index {dev.index}
                          </span>
                          <span className="text-xs font-semibold">{dev.name}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 text-[11px] text-gray-500 font-mono">
                        <span>{dev.resolution}</span>
                        {dev.available && (
                          <span className="bg-green-100 text-green-800 px-1.5 py-0.5 rounded text-[10px] font-bold">
                            ONLINE
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Index Button Selector & Manual Input */}
            <div className="pt-2 border-t border-gray-200 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-gray-700 block mb-1">
                  Quick Index Selection:
                </span>
                <div className="flex items-center space-x-1.5">
                  {[0, 1, 2, 3, 4].map((idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setSelectedIndex(idx)}
                      className={`w-9 h-8 rounded text-xs font-mono font-bold border transition-colors ${
                        selectedIndex === idx
                          ? 'bg-[#2B579A] text-white border-[#2B579A] shadow-sm'
                          : 'bg-gray-100 hover:bg-white text-gray-700 border-gray-300'
                      }`}
                    >
                      {idx}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-[11px] font-semibold text-gray-700 block mb-1">
                  Manual Index:
                </span>
                <div className="flex items-center space-x-1">
                  <input
                    type="number"
                    min={0}
                    max={16}
                    value={selectedIndex}
                    onChange={(e) => setSelectedIndex(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-20 px-2 py-1 text-xs border border-gray-400 rounded font-mono text-center font-bold bg-white"
                  />
                </div>
              </div>
            </div>

            {/* Resolution Setting */}
            <div className="pt-2 border-t border-gray-200">
              <span className="text-[11px] font-semibold text-gray-700 block mb-1.5">
                Camera Capture Resolution:
              </span>
              <div className="grid grid-cols-3 gap-2 text-xs">
                {[
                  { label: '1280 x 720 (HD - Recommended)', w: 1280, h: 720 },
                  { label: '1920 x 1080 (Full HD)', w: 1920, h: 1080 },
                  { label: '640 x 480 (VGA Standard)', w: 640, h: 480 }
                ].map((res) => (
                  <button
                    key={res.label}
                    type="button"
                    onClick={() => setResolution({ width: res.w, height: res.h })}
                    className={`p-2 rounded border text-left transition-colors ${
                      resolution.width === res.w && resolution.height === res.h
                        ? 'bg-blue-50 border-[#2B579A] text-blue-900 font-semibold ring-1 ring-[#2B579A]'
                        : 'bg-gray-50 border-gray-300 text-gray-700 hover:bg-white'
                    }`}
                  >
                    <div className="font-mono text-[11px] font-bold">{res.w} x {res.h}</div>
                    <div className="text-[10px] text-gray-500 truncate">{res.label.split('(')[1]?.replace(')', '') || ''}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Current Hardware Info Banner */}
          <div className="bg-gray-200 p-2.5 rounded text-[11px] text-gray-700 flex items-center justify-between border border-gray-300">
            <span className="font-semibold">Active Hardware Configuration:</span>
            <span className="font-mono bg-white px-2 py-0.5 rounded border border-gray-300 text-gray-800 font-bold">
              {currentStatus
                ? `USB Camera | Index [${currentStatus.device_index}] | ${currentStatus.resolution}`
                : 'Loading camera status...'}
            </span>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="bg-[#EDEBE9] px-4 py-3 flex items-center justify-between border-t border-[#D2D0CE]">
          <div className="text-[11px] text-gray-500">
            Changes take effect immediately on the live conveyor viewport.
          </div>
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-100 font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleApply}
              disabled={isApplying}
              className="px-4 py-1.5 text-xs text-white bg-[#107C10] hover:bg-[#0E6032] border border-green-700 rounded font-bold shadow-sm transition-colors flex items-center space-x-1.5 disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{isApplying ? 'Connecting...' : 'Connect Camera'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
