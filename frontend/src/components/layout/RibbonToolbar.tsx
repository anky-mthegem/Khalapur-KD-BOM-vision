import React from 'react';
import {
  Play,
  RotateCcw,
  Sliders,
  CheckCircle2,
  FileSpreadsheet,
  Upload,
  RefreshCw,
  Tag,
  Crosshair,
  Save,
  Boxes,
  History,
  Sparkles,
  Camera,
  Layers,
  ArrowRightLeft,
  HelpCircle
} from 'lucide-react';

export type RibbonTab = 'home' | 'recipes' | 'labeling' | 'training' | 'audit';

interface RibbonToolbarProps {
  activeTab: RibbonTab;
  onSelectTab: (tab: RibbonTab) => void;
  // Home actions
  onScanMasterCode: (code: string) => void;
  onResetCounts: () => void;
  onToggleTripwireMode: () => void;
  isTripwireEditMode: boolean;
  onCompleteBatch: () => void;
  onOpenUploadModal: () => void;
  // Camera actions
  cameraMode?: string;
  cameraIndex?: number;
  onSwitchCamera?: (mode: string, index?: number) => void;
  onOpenCameraSettings?: () => void;
  // Labeling actions
  onCaptureFrame?: () => void;
  onAutoAnnotate?: () => void;
  onSaveAnnotations?: () => void;
}

export const RibbonToolbar: React.FC<RibbonToolbarProps> = ({
  activeTab,
  onSelectTab,
  onScanMasterCode,
  onResetCounts,
  onToggleTripwireMode,
  isTripwireEditMode,
  onCompleteBatch,
  onOpenUploadModal,
  cameraMode = 'SYNTHETIC',
  cameraIndex = 0,
  onSwitchCamera,
  onOpenCameraSettings,
  onCaptureFrame,
  onAutoAnnotate,
  onSaveAnnotations
}) => {
  const [barcodeInput, setBarcodeInput] = React.useState('');

  const handleBarcodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (barcodeInput.trim()) {
      onScanMasterCode(barcodeInput.trim());
      setBarcodeInput('');
    }
  };

  return (
    <div className="bg-[#F3F2F1] border-b border-[#D2D0CE] shadow-sm select-none">
      {/* 1. Ribbon Tabs Header */}
      <div className="flex items-center justify-between border-b border-[#D2D0CE] bg-[#EDEBE9] px-2 text-xs">
        <div className="flex">
          <button
            onClick={() => onSelectTab('home')}
            className={`ribbon-tab ${activeTab === 'home' ? 'ribbon-tab-active' : 'ribbon-tab-inactive'}`}
          >
            Home / Inspection
          </button>
          <button
            onClick={() => onSelectTab('recipes')}
            className={`ribbon-tab ${activeTab === 'recipes' ? 'ribbon-tab-active' : 'ribbon-tab-inactive'}`}
          >
            BOM Recipes
          </button>
          <button
            onClick={() => onSelectTab('labeling')}
            className={`ribbon-tab ${activeTab === 'labeling' ? 'ribbon-tab-active' : 'ribbon-tab-inactive'}`}
          >
            Dataset & Labeling
          </button>
          <button
            onClick={() => onSelectTab('training')}
            className={`ribbon-tab ${activeTab === 'training' ? 'ribbon-tab-active' : 'ribbon-tab-inactive'}`}
          >
            Model Training
          </button>
          <button
            onClick={() => onSelectTab('audit')}
            className={`ribbon-tab ${activeTab === 'audit' ? 'ribbon-tab-active' : 'ribbon-tab-inactive'}`}
          >
            Audit Logs
          </button>
        </div>

        <a
          href="/manual/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center space-x-1.5 text-[#2B579A] hover:text-[#107C10] hover:bg-white px-2.5 py-1 rounded border border-transparent hover:border-gray-300 font-semibold transition-colors"
          title="Open Standard Operating Procedure (SOP) & User Manual"
        >
          <HelpCircle className="w-3.5 h-3.5 text-[#2B579A]" />
          <span>Help & SOP Manual</span>
        </a>
      </div>

      {/* 2. Ribbon Action Body */}
      <div className="h-[84px] px-3 py-1 flex items-center bg-[#F3F2F1] overflow-x-auto">
        {activeTab === 'home' && (
          <div className="flex items-center space-x-1">
            {/* Barcode / Master Code Group */}
            <div className="flex flex-col justify-center pr-2">
              <span className="text-[10px] uppercase font-bold text-gray-500 mb-1">Recipe Trigger</span>
              <form onSubmit={handleBarcodeSubmit} className="flex items-center space-x-1">
                <input
                  type="text"
                  placeholder="Scan Master Code / Barcode..."
                  value={barcodeInput}
                  onChange={(e) => setBarcodeInput(e.target.value)}
                  className="px-2 py-1 text-xs border border-gray-400 rounded w-48 font-mono focus:outline-none focus:border-[#2B579A] bg-white"
                />
                <button
                  type="submit"
                  className="bg-[#2B579A] hover:bg-[#1E3E6D] text-white px-2 py-1 rounded text-xs font-semibold"
                >
                  Load
                </button>
              </form>
            </div>

            <div className="ribbon-divider" />

            {/* Verification & QC Actions */}
            <button
              onClick={onCompleteBatch}
              className="ribbon-btn-large bg-green-50 border-green-300 text-[#107C10] hover:bg-green-100"
              title="Verify 100% BOM match, log audit record, and trigger QC label"
            >
              <CheckCircle2 className="w-5 h-5 text-[#107C10] mb-0.5" />
              <span className="font-bold text-[#107C10]">Complete Batch</span>
              <span className="text-[9px] text-gray-600">Print QC Label</span>
            </button>

            <button
              onClick={onResetCounts}
              className="ribbon-btn-large"
              title="Reset current session counts to zero"
            >
              <RotateCcw className="w-5 h-5 text-gray-700 mb-0.5" />
              <span>Reset</span>
              <span className="text-[9px] text-gray-500">Counts</span>
            </button>

            <div className="ribbon-divider" />

            {/* Tripwire Setup */}
            <button
              onClick={onToggleTripwireMode}
              className={`ribbon-btn-large ${isTripwireEditMode ? 'bg-cyan-100 border-cyan-400 text-cyan-800' : ''}`}
              title="Drag tripwire handles directly on video canvas"
            >
              <Sliders className="w-5 h-5 text-cyan-700 mb-0.5" />
              <span>Tripwire</span>
              <span className="text-[9px] text-gray-500">{isTripwireEditMode ? 'Editing' : 'Adjust'}</span>
            </button>

            <div className="ribbon-divider" />

            <button
              onClick={onOpenUploadModal}
              className="ribbon-btn-large"
              title="Import plant BOM Excel sheet (.xlsx)"
            >
              <Upload className="w-5 h-5 text-[#107C41] mb-0.5" />
              <span>Import BOM</span>
              <span className="text-[9px] text-gray-500">Excel (.xlsx)</span>
            </button>

            <div className="ribbon-divider" />

            {/* Live Camera Source & Index Selector Group */}
            <div className="flex flex-col justify-center px-1">
              <span className="text-[10px] uppercase font-bold text-gray-500 mb-1 flex items-center space-x-1">
                <Camera className="w-3.5 h-3.5 text-[#2B579A]" />
                <span>Camera Source</span>
              </span>
              <div className="flex items-center space-x-1.5">
                <select
                  value={cameraMode === 'USB' ? `USB_${cameraIndex}` : 'SYNTHETIC'}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === 'SETTINGS') {
                      onOpenCameraSettings && onOpenCameraSettings();
                    } else if (val === 'SYNTHETIC') {
                      onSwitchCamera && onSwitchCamera('SYNTHETIC');
                    } else if (val.startsWith('USB_')) {
                      const idx = parseInt(val.split('_')[1], 10);
                      onSwitchCamera && onSwitchCamera('USB', idx);
                    }
                  }}
                  className="px-2 py-1 text-xs border border-gray-400 rounded bg-white font-semibold text-gray-800 focus:outline-none focus:border-[#2B579A] shadow-sm cursor-pointer"
                >
                  <option value="USB_0">📹 USB Camera [Index 0]</option>
                  <option value="USB_1">📹 USB Camera [Index 1]</option>
                  <option value="USB_2">📹 USB Camera [Index 2]</option>
                  <option value="USB_3">📹 USB Camera [Index 3]</option>
                  <option value="SYNTHETIC">⚙️ Synthetic Simulator</option>
                  <option value="SETTINGS">⚙️ Camera Settings & Scan...</option>
                </select>

                <button
                  type="button"
                  onClick={onOpenCameraSettings}
                  className="ribbon-btn-large bg-blue-50/70 border-blue-200 text-blue-900 hover:bg-blue-100"
                  title="Configure camera hardware, resolution, or probe device index"
                >
                  <Sliders className="w-4 h-4 text-[#2B579A] mb-0.5" />
                  <span className="font-bold text-[#2B579A]">Camera Setup</span>
                  <span className="text-[9px] text-gray-500">Index & Ports</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'recipes' && (
          <div className="flex items-center space-x-1">
            <button
              onClick={onOpenUploadModal}
              className="ribbon-btn-large bg-green-50 border-green-300 hover:bg-green-100"
            >
              <FileSpreadsheet className="w-5 h-5 text-[#107C41] mb-0.5" />
              <span className="font-bold text-[#107C41]">Import Excel BOM</span>
              <span className="text-[9px] text-gray-600">New Kit Recipe</span>
            </button>
            <div className="ribbon-divider" />
            <div className="text-xs text-gray-600 px-2 max-w-sm">
              <span className="font-semibold text-gray-800">Plant Recipe Registry:</span> Manage manufacturing BOM kits, review drawing numbers, inspect auto-excluded packaging items, and sync new items with the YOLO vision catalog.
            </div>
          </div>
        )}

        {activeTab === 'labeling' && (
          <div className="flex items-center space-x-1">
            <button
              onClick={onCaptureFrame}
              className="ribbon-btn-large bg-blue-50 border-blue-200 hover:bg-blue-100"
            >
              <Camera className="w-5 h-5 text-blue-700 mb-0.5" />
              <span className="font-bold text-blue-800">Capture Frame</span>
              <span className="text-[9px] text-gray-600">From Conveyor</span>
            </button>

            <button
              onClick={onAutoAnnotate}
              className="ribbon-btn-large"
            >
              <Sparkles className="w-5 h-5 text-purple-600 mb-0.5" />
              <span>Auto Contour</span>
              <span className="text-[9px] text-gray-500">OpenCV OBB</span>
            </button>

            <button
              onClick={onSaveAnnotations}
              className="ribbon-btn-large bg-green-50 border-green-200 hover:bg-green-100"
            >
              <Save className="w-5 h-5 text-green-700 mb-0.5" />
              <span className="font-bold text-green-800">Save Labels</span>
              <span className="text-[9px] text-gray-600">YOLO-OBB Format</span>
            </button>
          </div>
        )}

        {activeTab === 'training' && (
          <div className="flex items-center space-x-1">
            <div className="text-xs text-gray-600 px-2">
              <span className="font-semibold text-gray-800">Ultralytics YOLO26 Pipeline:</span> Configure base model weights (`yolo26s-obb.pt`), run background training, view mAP50 convergence, and hot-swap active weights live into the conveyor inspector.
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="flex items-center space-x-1">
            <div className="text-xs text-gray-600 px-2">
              <span className="font-semibold text-gray-800">Plant Quality Audit Logs:</span> Chronological record of completed inspection batches, pass/fail results, missing hardware discrepancies, and high-resolution verification snapshots.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
