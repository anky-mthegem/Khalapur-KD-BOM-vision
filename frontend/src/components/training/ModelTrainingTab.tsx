import React, { useState, useEffect } from 'react';
import { Play, CheckCircle2, Cpu, RefreshCw, Zap, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { TrainingStatus, ModelWeightFile } from '../../types/bom';

interface ModelTrainingTabProps {
  activeModelName: string;
  onModelActivated: (name: string) => void;
}

export const ModelTrainingTab: React.FC<ModelTrainingTabProps> = ({
  activeModelName,
  onModelActivated
}) => {
  const [baseModel, setBaseModel] = useState("yolo26s-obb.pt");
  const [epochs, setEpochs] = useState(50);
  const [imgsz, setImgsz] = useState(1280);
  const [device, setDevice] = useState("auto");
  const [status, setStatus] = useState<TrainingStatus | null>(null);
  const [models, setModels] = useState<ModelWeightFile[]>([]);
  const [isStarting, setIsStarting] = useState(false);

  const fetchStatusAndModels = async () => {
    try {
      const [st, mdls] = await Promise.all([
        api.getTrainingStatus(),
        api.listModels()
      ]);
      setStatus(st);
      setModels(mdls);
    } catch (e) {
      console.error("Training status fetch error:", e);
    }
  };

  useEffect(() => {
    fetchStatusAndModels();
    const interval = setInterval(fetchStatusAndModels, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStartTraining = async () => {
    setIsStarting(true);
    try {
      await api.startTraining({
        base_model: baseModel,
        epochs,
        imgsz,
        device
      });
      fetchStatusAndModels();
    } catch (e: any) {
      alert("Error starting training: " + e.message);
    } finally {
      setIsStarting(false);
    }
  };

  const handleActivate = async (filename: string) => {
    try {
      await api.activateModel(filename);
      onModelActivated(filename);
      fetchStatusAndModels();
    } catch (e: any) {
      alert("Error activating model: " + e.message);
    }
  };

  const isTraining = status?.status === 'RUNNING';
  const progressPct = status && status.total_epochs > 0 ? (status.current_epoch / status.total_epochs) * 100 : 0;

  return (
    <div className="flex-1 bg-white p-6 overflow-y-auto text-xs select-none">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="border-b border-gray-200 pb-3 flex justify-between items-center">
          <div>
            <h2 className="text-base font-bold text-gray-800">Ultralytics YOLO26-OBB Training Pipeline</h2>
            <p className="text-gray-500 text-xs">
              Automated fine-tuning using persistent class mappings from the Global Parts Catalog with native end-to-end inference (nms=False).
            </p>
          </div>
          <button
            onClick={fetchStatusAndModels}
            className="flex items-center space-x-1 px-3 py-1 bg-gray-100 hover:bg-gray-200 border rounded text-gray-700"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Configuration Panel */}
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-300 grid grid-cols-4 gap-4">
          <div>
            <label className="font-semibold text-gray-700 block mb-1">Base OBB Architecture:</label>
            <select
              value={baseModel}
              onChange={(e) => setBaseModel(e.target.value)}
              disabled={isTraining}
              className="w-full p-2 border border-gray-300 rounded bg-white font-mono text-xs"
            >
              <option value="yolo26n-obb.pt">yolo26n-obb.pt (Nano - Fastest)</option>
              <option value="yolo26s-obb.pt">yolo26s-obb.pt (Small - Recommended)</option>
              <option value="yolo26m-obb.pt">yolo26m-obb.pt (Medium - High Accuracy)</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-gray-700 block mb-1">Training Epochs:</label>
            <input
              type="number"
              value={epochs}
              onChange={(e) => setEpochs(parseInt(e.target.value) || 10)}
              disabled={isTraining}
              className="w-full p-2 border border-gray-300 rounded bg-white font-mono text-xs"
              min="5"
              max="300"
            />
          </div>

          <div>
            <label className="font-semibold text-gray-700 block mb-1">Image Size (imgsz):</label>
            <select
              value={imgsz}
              onChange={(e) => setImgsz(parseInt(e.target.value))}
              disabled={isTraining}
              className="w-full p-2 border border-gray-300 rounded bg-white font-mono text-xs"
            >
              <option value={1280}>1280 (High Res - Fastener Threads)</option>
              <option value={640}>640 (Standard)</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-gray-700 block mb-1">Compute Device:</label>
            <select
              value={device}
              onChange={(e) => setDevice(e.target.value)}
              disabled={isTraining}
              className="w-full p-2 border border-gray-300 rounded bg-white font-mono text-xs"
            >
              <option value="auto">Auto Detect (CUDA / CPU)</option>
              <option value="0">CUDA GPU 0</option>
              <option value="cpu">CPU Only</option>
            </select>
          </div>

          <div className="col-span-4 flex justify-end">
            <button
              onClick={handleStartTraining}
              disabled={isTraining || isStarting}
              className={`px-5 py-2 rounded font-bold text-white flex items-center space-x-2 shadow ${isTraining ? 'bg-gray-400 cursor-not-allowed' : 'bg-[#2B579A] hover:bg-[#1E3E6D]'}`}
            >
              <Play className="w-4 h-4 fill-white" />
              <span>{isTraining ? 'Training in Progress...' : 'Start YOLO26-OBB Training'}</span>
            </button>
          </div>
        </div>

        {/* Live Training Status Progress Card */}
        {status && (
          <div className="bg-white p-4 rounded-lg border border-gray-300 space-y-3 shadow-sm">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-[#2B579A]" />
                <span className="font-bold text-sm text-gray-800">
                  Status: <span className="font-mono text-[#2B579A]">{status.status}</span>
                </span>
              </div>
              <span className="font-mono text-gray-600">
                Epoch: <strong>{status.current_epoch} / {status.total_epochs}</strong>
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 h-3 rounded-full overflow-hidden">
              <div
                className="bg-[#2B579A] h-full transition-all duration-300"
                style={{ width: `${progressPct}%` }}
              />
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-4 gap-3 text-center font-mono pt-2">
              <div className="bg-gray-50 p-2 rounded border">
                <span className="text-[10px] text-gray-500 block">TRAINING LOSS</span>
                <span className="text-sm font-bold text-gray-800">{status.loss.toFixed(4)}</span>
              </div>
              <div className="bg-gray-50 p-2 rounded border">
                <span className="text-[10px] text-gray-500 block">mAP50</span>
                <span className="text-sm font-bold text-[#107C10]">{(status.map50 * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-gray-50 p-2 rounded border">
                <span className="text-[10px] text-gray-500 block">mAP50-95</span>
                <span className="text-sm font-bold text-blue-700">{(status.map50_95 * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-gray-50 p-2 rounded border">
                <span className="text-[10px] text-gray-500 block">ACTIVE WEIGHTS</span>
                <span className="text-xs font-bold text-gray-700 truncate block" title={status.active_weights}>
                  {status.active_weights}
                </span>
              </div>
            </div>

            {/* Real-Time Terminal Progress Logs */}
            <div className="space-y-1 pt-1">
              <span className="text-[11px] font-bold text-gray-700 uppercase tracking-wider block">
                Ultralytics YOLO26 Training Progress Logs:
              </span>
              <div className="bg-gray-900 text-green-400 font-mono text-[11px] p-3 rounded h-36 overflow-y-auto border border-gray-700 space-y-0.5">
                {(status.logs && status.logs.length > 0) ? (
                  status.logs.map((logLine, idx) => (
                    <div key={idx} className="whitespace-pre-wrap">{logLine}</div>
                  ))
                ) : (
                  <div className="text-gray-500 italic">No active training logs. Ready to start.</div>
                )}
              </div>
            </div>

            {status.status === 'COMPLETED' && (
              <div className="bg-green-50 border border-green-300 text-green-800 p-2.5 rounded text-xs flex items-center justify-between">
                <span className="flex items-center space-x-1.5 font-bold">
                  <CheckCircle2 className="w-4 h-4 text-[#107C10]" />
                  <span>Training completed successfully! Model weights '{status.active_weights}' are now active.</span>
                </span>
              </div>
            )}
          </div>
        )}

        {/* Model Weight Artifacts & Hot-Swap Manager */}
        <div className="space-y-3">
          <h3 className="font-bold text-gray-800 text-sm">Model Weight Artifacts & Live Hot-Swap</h3>
          <div className="border border-gray-300 rounded overflow-hidden">
            <table className="excel-grid-table">
              <thead>
                <tr>
                  <th>Weights Filename</th>
                  <th className="w-24 text-center">File Size</th>
                  <th className="w-32 text-center">Status</th>
                  <th className="w-36 text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => {
                  const isActive = m.filename === activeModelName;
                  return (
                    <tr key={m.filename} className={isActive ? 'bg-green-50/70 font-semibold' : 'hover:bg-gray-50'}>
                      <td className="font-mono text-[#2B579A]">{m.filename}</td>
                      <td className="text-center font-mono text-gray-600">{m.size_mb} MB</td>
                      <td className="text-center">
                        {isActive ? (
                          <span className="badge-pass">ACTIVE ON BELT</span>
                        ) : (
                          <span className="badge-pending">STANDBY</span>
                        )}
                      </td>
                      <td className="text-center">
                        {!isActive && (
                          <button
                            onClick={() => handleActivate(m.filename)}
                            className="px-2.5 py-1 bg-[#107C10] hover:bg-[#0E6A0E] text-white rounded font-bold text-[11px] inline-flex items-center space-x-1"
                          >
                            <Zap className="w-3 h-3 fill-white" />
                            <span>Activate Model</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {models.length === 0 && (
                  <tr>
                    <td colSpan={4} className="text-center py-4 text-gray-500 italic">
                      No custom trained weights yet. System running on base {activeModelName}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
