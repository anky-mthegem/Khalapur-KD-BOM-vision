import React, { useState, useEffect } from 'react';
import { TitleBar } from './components/layout/TitleBar';
import { RibbonToolbar, RibbonTab } from './components/layout/RibbonToolbar';
import { StatusBar } from './components/layout/StatusBar';
import { ConveyorViewport } from './components/inspection/ConveyorViewport';
import { BomGrid } from './components/inspection/BomGrid';
import { QcAlertModal } from './components/inspection/QcAlertModal';
import { CameraSettingsModal } from './components/inspection/CameraSettingsModal';
import { ExcelUploadModal } from './components/bom/ExcelUploadModal';
import { BomRecipesTab } from './components/bom/BomRecipesTab';
import { LabelingStudioTab } from './components/labeling/LabelingStudioTab';
import { ModelTrainingTab } from './components/training/ModelTrainingTab';
import { AuditLogsTab } from './components/audit/AuditLogsTab';

import { api } from './services/api';
import { InspectionState, TripwireGeometry, QcVerificationResult, CameraStatus } from './types/bom';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<RibbonTab>('home');
  const [activeMasterCode, setActiveMasterCode] = useState<string>("31162814SD05076");
  const [activeModelName, setActiveModelName] = useState<string>("yolo26s-obb.pt");
  const [isTripwireEditMode, setIsTripwireEditMode] = useState<boolean>(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [isCameraModalOpen, setIsCameraModalOpen] = useState<boolean>(false);
  const [cameraStatus, setCameraStatus] = useState<CameraStatus | null>(null);
  const [qcResult, setQcResult] = useState<QcVerificationResult | null>(null);

  // Inspection State
  const [sessionState, setSessionState] = useState<InspectionState>({
    session_uid: null,
    master_item_code: "31162814SD05076",
    total_target: 68,
    total_counted: 0,
    overall_status: "IDLE",
    items: []
  });

  const [tripwire, setTripwire] = useState<TripwireGeometry>({
    coords: [0.55, 0.05, 0.55, 0.95],
    direction: "LEFT_TO_RIGHT"
  });

  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [fps, setFps] = useState<number>(29.8);
  const [totalBatches, setTotalBatches] = useState<number>(12);
  const [passCount, setPassCount] = useState<number>(11);

  // Initial load
  useEffect(() => {
    fetchSessionState();
    fetchTripwire();
    fetchCameraStatus();

    // WebSocket connection for real-time counts and hardware events
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/inspection`;
    let ws: WebSocket;

    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === 'STATE_UPDATE' || msg.event === 'INIT_STATE') {
            setSessionState(msg.data);
            if (msg.data.master_item_code) {
              setActiveMasterCode(msg.data.master_item_code);
            }
            if (msg.camera) {
              setCameraStatus(msg.camera);
            }
          } else if (msg.event === 'CAMERA_CHANGED') {
            setCameraStatus(msg.data);
          } else if (msg.event === 'TRIPWIRE_CROSS') {
            // Slight FPS vibration jitter simulation
            setFps(prev => Number((29.5 + Math.random() * 0.8).toFixed(1)));
          }
        } catch (e) {
          console.error("WS message parse error:", e);
        }
      };
    } catch (e) {
      console.warn("WebSocket fallback:", e);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const fetchCameraStatus = async () => {
    try {
      const status = await api.getCameraStatus();
      setCameraStatus(status);
    } catch (e) {
      console.warn("Failed to fetch camera status:", e);
    }
  };

  const handleSwitchCamera = async (mode: string, index?: number) => {
    try {
      const res = await api.switchCameraSource({ mode, device_index: index });
      setCameraStatus(res);
    } catch (e: any) {
      alert("Error switching camera source: " + e.message);
    }
  };

  const fetchSessionState = async () => {
    try {
      const state = await api.getCurrentSession();
      setSessionState(state);
      if (state.master_item_code) {
        setActiveMasterCode(state.master_item_code);
      }
    } catch (e) {
      console.error("Failed to fetch session state:", e);
    }
  };

  const fetchTripwire = async () => {
    try {
      const tw = await api.getTripwire();
      setTripwire(tw);
    } catch (e) {
      console.error("Failed to fetch tripwire:", e);
    }
  };

  const handleScanMasterCode = async (code: string) => {
    try {
      const res = await api.startInspection(code);
      setActiveMasterCode(code);
      setSessionState(res.state);
    } catch (e: any) {
      alert(`Master Code '${code}' not found: ${e.message}`);
    }
  };

  const handleResetCounts = async () => {
    try {
      const res = await api.resetCounts();
      setSessionState(res.state);
    } catch (e: any) {
      console.error("Reset counts error:", e);
    }
  };

  const handleUpdateTripwire = async (coords: [number, number, number, number]) => {
    try {
      await api.updateTripwire(coords, tripwire.direction);
      setTripwire(prev => ({ ...prev, coords }));
    } catch (e) {
      console.error("Failed to update tripwire geometry:", e);
    }
  };

  const handleCompleteBatch = async () => {
    try {
      const result = await api.completeBatch();
      setQcResult(result);
      setTotalBatches(prev => prev + 1);
      if (result.status === 'PASSED') {
        setPassCount(prev => prev + 1);
      }
      fetchSessionState();
    } catch (e: any) {
      alert("Error executing QC Gate: " + e.message);
    }
  };

  const handleToggleVision = async (srNo: number) => {
    // Optimistic toggle in local view
    setSessionState(prev => ({
      ...prev,
      items: prev.items.map(it => it.sr_no === srNo ? { ...it, is_vision_inspected: !it.is_vision_inspected } : it)
    }));
  };

  const cameraStatusText = cameraStatus
    ? (cameraStatus.mode === 'USB' ? `USB [${cameraStatus.device_index}]` : 'SIMULATOR')
    : 'OK (Conveyor)';
  const isCameraConnected = cameraStatus ? cameraStatus.is_connected : true;

  return (
    <div className="flex flex-col h-screen w-screen bg-[#F3F2F1] overflow-hidden select-none">
      {/* 1. Top Windows/Office Title Bar */}
      <TitleBar
        activeMasterCode={activeMasterCode}
        cameraStatus={cameraStatusText}
        isCameraConnected={isCameraConnected}
        onOpenCameraSettings={() => setIsCameraModalOpen(true)}
        modelName={activeModelName}
        plcStatus="PLC: READY"
      />

      {/* 2. MS Word-Style Ribbon Toolbar */}
      <RibbonToolbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onScanMasterCode={handleScanMasterCode}
        onResetCounts={handleResetCounts}
        onToggleTripwireMode={() => setIsTripwireEditMode(!isTripwireEditMode)}
        isTripwireEditMode={isTripwireEditMode}
        onCompleteBatch={handleCompleteBatch}
        onOpenUploadModal={() => setIsUploadModalOpen(true)}
        cameraMode={cameraStatus?.mode || 'SYNTHETIC'}
        cameraIndex={cameraStatus?.device_index ?? 0}
        onSwitchCamera={handleSwitchCamera}
        onOpenCameraSettings={() => setIsCameraModalOpen(true)}
      />

      {/* 3. Main Workspace Area */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'home' && (
          <div className="flex-1 flex w-full h-full overflow-hidden">
            {/* Left/Center (65%): Conveyor Viewport + Tripwire Canvas */}
            <ConveyorViewport
              streamUrl="/api/stream/mjpeg"
              tripwire={tripwire}
              onUpdateTripwire={handleUpdateTripwire}
              isTripwireEditMode={isTripwireEditMode}
              overallStatus={sessionState.overall_status}
              totalTarget={sessionState.total_target}
              totalCounted={sessionState.total_counted}
              zoomLevel={zoomLevel}
            />

            {/* Right (35%): Excel-Style Dense BOM Recipe Grid */}
            <BomGrid
              items={sessionState.items}
              onToggleVisionInspected={handleToggleVision}
              masterItemCode={activeMasterCode}
            />
          </div>
        )}

        {activeTab === 'recipes' && (
          <BomRecipesTab
            onLoadRecipe={(code) => {
              handleScanMasterCode(code);
              setActiveTab('home');
            }}
            activeMasterCode={activeMasterCode}
          />
        )}

        {activeTab === 'labeling' && (
          <LabelingStudioTab activeMasterCode={activeMasterCode} />
        )}

        {activeTab === 'training' && (
          <ModelTrainingTab
            activeModelName={activeModelName}
            onModelActivated={(name) => setActiveModelName(name)}
          />
        )}

        {activeTab === 'audit' && (
          <AuditLogsTab />
        )}
      </div>

      {/* 4. Bottom Status Bar (MS Word Blue) */}
      <StatusBar
        fps={fps}
        latencyMs={14}
        activeModelName={activeModelName}
        totalBatches={totalBatches}
        passCount={passCount}
        zoomLevel={zoomLevel}
        onZoomIn={() => setZoomLevel(prev => Math.min(160, prev + 10))}
        onZoomOut={() => setZoomLevel(prev => Math.max(60, prev - 10))}
      />

      {/* Modals */}
      <CameraSettingsModal
        isOpen={isCameraModalOpen}
        onClose={() => setIsCameraModalOpen(false)}
        onSourceChanged={(status) => setCameraStatus(status)}
        currentStatus={cameraStatus}
      />

      <ExcelUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onRecipeCommitted={(code) => {
          handleScanMasterCode(code);
          setActiveTab('home');
        }}
      />

      <QcAlertModal
        result={qcResult}
        onClose={() => setQcResult(null)}
        onPrintLabel={() => {
          alert(`Sending print payload to Zebra ZD421 Industrial QC Label Printer: [${activeMasterCode}] PASS - ${sessionState.total_counted} PCS.`);
        }}
      />
    </div>
  );
};
export default App;
