export interface BomRecipeItem {
  id?: number;
  sr_no: number;
  part_uid: string;
  item_name: string;
  drawing_no: string;
  target_qty: number;
  is_vision_inspected: boolean;
}

export interface BomRecipe {
  id: number;
  master_item_code: string;
  description: string;
  total_items: number;
  vision_items_count: number;
  items: BomRecipeItem[];
  created_at?: string;
  updated_at?: string;
}

export interface BomPreviewItem {
  sr_no: number;
  part_uid: string;
  item_name: string;
  drawing_no: string;
  target_qty: number;
  is_vision_inspected: boolean;
  is_new_part: boolean;
  training_status: string;
}

export interface BomPreviewResponse {
  master_item_code: string;
  description: string;
  sheet_name: string;
  total_items: number;
  vision_items_count: number;
  excluded_packaging_count: number;
  new_parts_count: number;
  items: BomPreviewItem[];
}

export interface PartCatalogItem {
  id: number;
  part_uid: string;
  item_name: string;
  drawing_no: string;
  yolo_class_id: number;
  training_status: "UNTRAINED" | "LABELED" | "TRAINED";
  sample_count: number;
}

export interface InspectionItemStatus {
  sr_no: number;
  part_uid: string;
  item_name: string;
  drawing_no: string;
  target_qty: number;
  counted_qty: number;
  is_vision_inspected: boolean;
  status: "PENDING" | "IN_PROGRESS" | "MATCH" | "OVERCOUNT" | "EXCLUDED";
}

export interface InspectionState {
  session_uid: string | null;
  master_item_code: string | null;
  total_target: number;
  total_counted: number;
  overall_status: "PASS" | "IN_PROGRESS" | "IDLE";
  items: InspectionItemStatus[];
}

export interface TripwireGeometry {
  coords: [number, number, number, number]; // [x1, y1, x2, y2]
  direction: "LEFT_TO_RIGHT" | "RIGHT_TO_LEFT";
}

export interface QcVerificationResult {
  status: "PASSED" | "BLOCKED";
  session_uid: string;
  total_target: number;
  total_counted: number;
  missing_items: Array<{
    drawing_no: string;
    item_name: string;
    target_qty: number;
    counted_qty: number;
    missing_qty: number;
  }>;
  overcounted_items: Array<{
    drawing_no: string;
    item_name: string;
    target_qty: number;
    counted_qty: number;
    over_qty: number;
  }>;
  snapshot_url?: string;
  qc_token?: string;
  message: string;
}

export interface TrainingStatus {
  status: "IDLE" | "RUNNING" | "COMPLETED" | "FAILED";
  run_name: string | null;
  current_epoch: number;
  total_epochs: number;
  loss: number;
  map50: number;
  map50_95: number;
  active_weights: string;
  last_error?: string;
  logs?: string[];
}

export interface DatasetSample {
  filename: string;
  stem: string;
  labels: string[];
  primary_label: string;
  timestamp: string;
}

export interface PartSummaryItem {
  item_name: string;
  drawing_no: string;
  yolo_class_id: number;
  sample_count: number;
  training_status: string;
}

export interface DatasetSummary {
  total_images: number;
  samples: DatasetSample[];
  parts_summary: PartSummaryItem[];
}

export interface ModelWeightFile {
  filename: string;
  path: string;
  size_mb: number;
  is_active: boolean;
}

export interface AuditSessionLog {
  id: number;
  session_uid: string;
  master_item_code: string;
  start_time: string;
  end_time: string | null;
  status: string;
  total_target: number;
  total_counted: number;
  snapshot_path: string | null;
  operator_notes: string | null;
}

export interface CameraDevice {
  index: number;
  name: string;
  resolution: string;
  available: boolean;
  is_current: boolean;
}

export interface CameraDevicesResponse {
  current_mode: "USB" | "SYNTHETIC" | "RTSP" | "FILE";
  current_index: number;
  source_type: string;
  is_connected: boolean;
  devices: CameraDevice[];
}

export interface CameraStatus {
  status: "CONNECTED" | "WARNING_NO_SIGNAL";
  mode: "USB" | "SYNTHETIC" | "RTSP" | "FILE";
  device_index: number;
  source_type: string;
  is_connected: boolean;
  resolution: string;
  target_fps: number;
}

