import {
  BomRecipe,
  BomPreviewResponse,
  PartCatalogItem,
  InspectionState,
  TripwireGeometry,
  QcVerificationResult,
  TrainingStatus,
  ModelWeightFile,
  AuditSessionLog
} from '../types/bom';

const API_BASE = '/api';

export const api = {
  // BOM Endpoints
  async uploadBomPreview(file: File): Promise<BomPreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/bom/upload-preview`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async parsePastedBom(rawText: string): Promise<BomPreviewResponse> {
    const res = await fetch(`${API_BASE}/bom/parse-pasted`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: rawText }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async commitBom(payload: { master_item_code: string; description: string; items: any[] }) {
    const res = await fetch(`${API_BASE}/bom/commit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async listRecipes(): Promise<BomRecipe[]> {
    const res = await fetch(`${API_BASE}/bom/recipes`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getRecipe(masterCode: string): Promise<BomRecipe> {
    const res = await fetch(`${API_BASE}/bom/recipes/${masterCode}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async toggleVisionInspected(itemId: number): Promise<{ id: number; is_vision_inspected: boolean }> {
    const res = await fetch(`${API_BASE}/bom/items/${itemId}/vision-toggle`, {
      method: 'PATCH',
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Parts Catalog
  async listParts(): Promise<PartCatalogItem[]> {
    const res = await fetch(`${API_BASE}/parts`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async listUntrainedParts(): Promise<PartCatalogItem[]> {
    const res = await fetch(`${API_BASE}/parts/untrained`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Inspection & Tripwire
  async startInspection(masterItemCode: string, operatorNotes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/inspection/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ master_item_code: masterItemCode, operator_notes: operatorNotes }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getCurrentSession(): Promise<InspectionState> {
    const res = await fetch(`${API_BASE}/inspection/current`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async resetCounts(): Promise<any> {
    const res = await fetch(`${API_BASE}/inspection/reset-counts`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getTripwire(): Promise<TripwireGeometry> {
    const res = await fetch(`${API_BASE}/inspection/tripwire`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateTripwire(coords: [number, number, number, number], direction: string = 'LEFT_TO_RIGHT'): Promise<any> {
    const res = await fetch(`${API_BASE}/inspection/tripwire`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        x1: coords[0],
        y1: coords[1],
        x2: coords[2],
        y2: coords[3],
        direction,
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async completeBatch(): Promise<QcVerificationResult> {
    const res = await fetch(`${API_BASE}/inspection/complete-batch`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async simulateCrossing(partUid: string, itemName: string = 'Test Item'): Promise<any> {
    const res = await fetch(`${API_BASE}/inspection/simulate-crossing?part_uid=${encodeURIComponent(partUid)}&item_name=${encodeURIComponent(itemName)}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Video Source
  async switchCameraSource(mode: string, pathOrIndex?: string) {
    const url = `${API_BASE}/stream/source?mode=${mode}${pathOrIndex ? `&path_or_index=${encodeURIComponent(pathOrIndex)}` : ''}`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Labeling Studio
  async captureFrame(): Promise<any> {
    const res = await fetch(`${API_BASE}/labeling/capture-frame`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async autoAnnotate(thresholdVal: number, blurKernel: number, minArea: number, maxArea: number): Promise<any> {
    const res = await fetch(`${API_BASE}/labeling/auto-annotate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        threshold_val: thresholdVal,
        blur_kernel: blurKernel,
        min_area: minArea,
        max_area: maxArea,
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async saveAnnotations(annotations: any[], masterItemCode?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/labeling/save-annotations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ annotations, master_item_code: masterItemCode }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async uploadComponentImage(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/labeling/upload-image`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async saveComponent(payload: {
    image_base64: string;
    item_name: string;
    drawing_no?: string;
    polygon?: number[][];
    master_item_code?: string;
  }): Promise<any> {
    const res = await fetch(`${API_BASE}/labeling/save-component`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getDatasetSummary(): Promise<any> {
    const res = await fetch(`${API_BASE}/labeling/dataset-summary`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async deleteSample(stem: string): Promise<any> {
    const res = await fetch(`${API_BASE}/labeling/sample/${encodeURIComponent(stem)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Training
  async startTraining(params: { base_model: string; epochs: number; imgsz: number; device: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/training/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getTrainingStatus(): Promise<TrainingStatus> {
    const res = await fetch(`${API_BASE}/training/status`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async activateModel(weightsName: string): Promise<any> {
    const res = await fetch(`${API_BASE}/training/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weights_path_or_name: weightsName }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async listModels(): Promise<ModelWeightFile[]> {
    const res = await fetch(`${API_BASE}/training/models`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Audit Logs
  async getAuditLogs(limit: number = 50): Promise<AuditSessionLog[]> {
    const res = await fetch(`${API_BASE}/audit/logs?limit=${limit}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};
