import React, { useState } from 'react';
import { Upload, X, Check, FileSpreadsheet, AlertTriangle, EyeOff, Save, Download, Clipboard, Trash2 } from 'lucide-react';
import { api } from '../../services/api';
import { BomPreviewResponse, BomPreviewItem } from '../../types/bom';

interface ExcelUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRecipeCommitted: (masterCode: string) => void;
}

export const ExcelUploadModal: React.FC<ExcelUploadModalProps> = ({
  isOpen,
  onClose,
  onRecipeCommitted
}) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [pastedText, setPastedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState<BomPreviewResponse | null>(null);
  const [previewItems, setPreviewItems] = useState<BomPreviewItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setError(null);
      setIsLoading(true);
      try {
        const previewData = await api.uploadBomPreview(selected);
        setPreview(previewData);
        setPreviewItems(previewData.items || []);
      } catch (err: any) {
        setError(err.message || 'Failed to parse Excel spreadsheet');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleParsePasted = async () => {
    if (!pastedText.trim()) {
      setError("Please paste BOM table data from Excel before parsing.");
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const previewData = await api.parsePastedBom(pastedText);
      setPreview(previewData);
      setPreviewItems(previewData.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to parse pasted BOM data. Ensure rows include Sr No, Item Name, and Qty.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteItem = (sr_no: number) => {
    setPreviewItems(prev => prev.filter(it => it.sr_no !== sr_no));
    setError(null);
  };

  const handleDrawingNoChange = (sr_no: number, val: string) => {
    setPreviewItems(prev => prev.map(it => {
      if (it.sr_no === sr_no) {
        const clean = val.trim().toUpperCase();
        const hasDwg = clean !== "" && clean !== "—" && clean !== "-" && clean !== "NA" && clean !== "N/A";
        return {
          ...it,
          drawing_no: val,
          part_uid: clean,
          has_drawing_no: hasDwg
        };
      }
      return it;
    }));
    setError(null);
  };

  // Calculations on current previewItems
  const missingDwgItems = previewItems.filter(it => {
    const dwg = (it.drawing_no || "").trim();
    return !dwg || dwg === "—" || dwg === "-" || dwg === "NA" || dwg === "N/A" || it.has_drawing_no === false;
  });
  const hasMissingDwg = missingDwgItems.length > 0;
  const currentTotalItems = previewItems.length;
  const currentVisionItems = previewItems.filter(it => it.is_vision_inspected).length;
  const currentExcludedCount = previewItems.filter(it => !it.is_vision_inspected).length;

  const handleCommit = async () => {
    if (!preview || previewItems.length === 0) return;
    if (hasMissingDwg) {
      setError(`Cannot save BOM: ${missingDwgItems.length} item(s) are missing a Drawing Number. Please delete these items using the trash icon or enter drawing numbers.`);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      await api.commitBom({
        master_item_code: preview.master_item_code,
        description: preview.description,
        items: previewItems.map((it, idx) => ({
          sr_no: idx + 1,
          part_uid: it.drawing_no.trim().toUpperCase(),
          item_name: it.item_name,
          drawing_no: it.drawing_no.trim().toUpperCase(),
          target_qty: it.target_qty,
          is_vision_inspected: it.is_vision_inspected,
        })),
      });
      onRecipeCommitted(preview.master_item_code);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save BOM recipe');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 select-none">
      <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden border border-gray-300">
        {/* Header */}
        <div className="bg-[#107C41] text-white p-3 px-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5 text-yellow-300" />
            <span className="font-bold text-sm">Create Manufacturing BOM Recipe from Standard Excel</span>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Template Helper Bar */}
        <div className="bg-green-50 border-b border-green-200 px-4 py-2.5 flex items-center justify-between">
          <div className="text-xs text-green-900">
            <strong>Standard Plant Format:</strong> Ensure BOM contains <em>Item Code(Master)</em>, <em>Description</em>, and line columns (<em>Sr No</em>, <em>Item Name</em>, <em>Drawing No</em>, <em>Qty</em>).
          </div>
          <a
            href="/api/bom/download-template"
            download="Standard_Plant_BOM_Template.xlsx"
            className="flex items-center space-x-1.5 bg-[#107C41] hover:bg-[#0E6032] text-white px-3 py-1 rounded text-xs font-semibold shadow-sm transition"
            title="Download standard Excel template with sample master kit"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Template (.xlsx)</span>
          </a>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex border-b border-gray-200 bg-gray-50 px-4 pt-2 space-x-2">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-t border-t border-x transition ${
              activeTab === 'upload'
                ? 'bg-white border-gray-300 text-[#107C41] border-b-white -mb-px'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            <span className="flex items-center space-x-1.5">
              <Upload className="w-3.5 h-3.5" />
              <span>Upload Standard Excel File</span>
            </span>
          </button>
          <button
            onClick={() => setActiveTab('paste')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-t border-t border-x transition ${
              activeTab === 'paste'
                ? 'bg-white border-gray-300 text-[#107C41] border-b-white -mb-px'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            <span className="flex items-center space-x-1.5">
              <Clipboard className="w-3.5 h-3.5" />
              <span>Copy-Paste BOM Table from Excel</span>
            </span>
          </button>
        </div>

        {/* Body */}
        <div className="p-4 flex-1 overflow-y-auto space-y-4 text-xs">
          {activeTab === 'upload' ? (
            /* File Selector */
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50/50 transition">
              <input
                type="file"
                id="excel-upload-input"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileChange}
                className="hidden"
              />
              <label htmlFor="excel-upload-input" className="cursor-pointer flex flex-col items-center">
                <Upload className="w-8 h-8 text-[#107C41] mb-2" />
                <span className="font-bold text-gray-800 text-sm">
                  {file ? file.name : "Click to select or drag & drop Standard Plant BOM (.xlsx / .csv)"}
                </span>
                <span className="text-[11px] text-gray-500 mt-1">
                  Supports multi-sheet workbooks with merged headers and auto-slugging of drawing numbers
                </span>
              </label>
            </div>
          ) : (
            /* Paste Text Area */
            <div className="space-y-2">
              <label className="font-semibold text-gray-700 block">
                Paste tabular data directly from Microsoft Excel (Ctrl+V):
              </label>
              <textarea
                value={pastedText}
                onChange={(e) => setPastedText(e.target.value)}
                placeholder={"Item Code(Master)\t31162814SD05076\nDescription\tHRD PKT FOR MAIN BODY 900W/1200W 560D KREATION X3\nSr No\tItem Name\tDrawing No\tQty\n1\tM4X10 SCREW CHEESE HEAD\tHOM196273\t8\n2\tM4 SLEEVE CONNECTING SCREW\t—\t2\n..."}
                rows={6}
                className="w-full p-2.5 border border-gray-300 rounded font-mono text-[11px] bg-gray-50 focus:bg-white focus:outline-none focus:border-[#107C41]"
              />
              <div className="flex justify-between items-center pt-1">
                <span className="text-[11px] text-gray-500">
                  Tip: Copy rows directly from Excel. Tab-separated cells will be automatically converted to BOM items.
                </span>
                <button
                  onClick={handleParsePasted}
                  disabled={isLoading}
                  className="px-4 py-1.5 bg-[#107C41] hover:bg-[#0E6032] text-white rounded font-bold text-xs flex items-center space-x-1.5 shadow"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Parse Pasted BOM</span>
                </button>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="text-center py-3 text-[#107C41] font-semibold animate-pulse">
              Processing BOM layout, verifying drawing numbers, and flagging packaging items...
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Preview Details */}
          {preview && (
            <div className="space-y-3">
              {/* Warning Banner if items have missing Drawing Numbers */}
              {hasMissingDwg && (
                <div className="bg-amber-50 border-l-4 border-amber-500 p-3 rounded text-xs text-amber-900 shadow-sm flex items-start space-x-2.5">
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <span className="font-bold text-amber-950 text-sm">
                      Warning: {missingDwgItems.length} item(s) are missing a Drawing Number!
                    </span>
                    <p className="text-amber-800 text-[11px] leading-relaxed">
                      Every item in the BOM must have a Drawing Number to be registered as a unique class in the YOLO model, database, and conveyor tripwire.
                      You can <strong>delete items without drawing numbers</strong> using the red trash icon (<Trash2 className="w-3.5 h-3.5 inline text-red-600 mx-0.5" />), or type a Drawing Number directly in the table.
                    </p>
                  </div>
                </div>
              )}

              <div className="bg-gray-50 p-3 rounded border border-gray-300 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Master Item Code:</span>{" "}
                  <strong className="font-mono text-[#2B579A] text-sm">{preview.master_item_code}</strong>
                </div>
                <div>
                  <span className="text-gray-500">Source:</span> <strong>{preview.sheet_name}</strong>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">Description:</span> <strong>{preview.description}</strong>
                </div>
                <div>
                  <span className="text-gray-500">Total Items:</span> <strong>{currentTotalItems}</strong> (Vision Inspected: {currentVisionItems})
                </div>
                <div>
                  <span className="text-gray-500">Auto-Excluded Packaging (Carton):</span> <strong className="text-gray-600">{currentExcludedCount}</strong>
                </div>
              </div>

              {/* Table Preview */}
              <div className="border border-gray-300 rounded overflow-hidden max-h-56 overflow-y-auto">
                <table className="excel-grid-table">
                  <thead className="sticky top-0 bg-[#F3F2F1]">
                    <tr>
                      <th className="w-8 text-center">#</th>
                      <th>Item Name</th>
                      <th>Drawing No (Unique Key)</th>
                      <th className="w-10 text-center">Qty</th>
                      <th className="w-14 text-center">Vision</th>
                      <th className="w-16 text-center">Status</th>
                      <th className="w-12 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {previewItems.map((it, idx) => {
                      const isDwgMissing = !it.drawing_no || it.drawing_no === '—' || it.drawing_no === '-' || it.drawing_no === 'NA' || it.has_drawing_no === false;
                      return (
                        <tr
                          key={it.sr_no || idx}
                          className={
                            isDwgMissing
                              ? "bg-amber-50/80 border-l-2 border-amber-500"
                              : it.is_vision_inspected
                              ? "bg-white"
                              : "bg-gray-100 text-gray-500 italic"
                          }
                        >
                          <td className="text-center font-mono">{idx + 1}</td>
                          <td className="truncate max-w-xs font-medium">{it.item_name}</td>
                          <td>
                            {isDwgMissing ? (
                              <div className="flex items-center space-x-1">
                                <input
                                  type="text"
                                  value={it.drawing_no === '—' || it.drawing_no === '-' ? '' : it.drawing_no}
                                  onChange={(e) => handleDrawingNoChange(it.sr_no, e.target.value)}
                                  placeholder="Enter Drawing No"
                                  className="w-36 px-1.5 py-0.5 border border-amber-400 bg-white rounded font-mono text-[11px] focus:outline-none focus:ring-1 focus:ring-amber-500"
                                />
                                <span className="text-[9px] font-bold bg-amber-200 text-amber-900 px-1 py-0.5 rounded whitespace-nowrap">
                                  REQUIRED
                                </span>
                              </div>
                            ) : (
                              <span className="font-mono font-bold text-[11px] text-[#2B579A]">{it.drawing_no}</span>
                            )}
                          </td>
                          <td className="text-center font-bold font-mono">{it.target_qty}</td>
                          <td className="text-center">
                            {it.is_vision_inspected ? (
                              <span className="text-green-700 font-bold">YES</span>
                            ) : (
                              <span className="badge-excluded flex items-center justify-center">
                                <EyeOff className="w-3 h-3 mr-0.5" /> EXCL
                              </span>
                            )}
                          </td>
                          <td className="text-center">
                            {isDwgMissing ? (
                              <span className="bg-amber-100 text-amber-800 font-bold px-1.5 py-0.5 rounded text-[10px]">
                                NO DWG
                              </span>
                            ) : it.is_new_part ? (
                              <span className="bg-blue-100 text-blue-800 font-bold px-1.5 py-0.5 rounded text-[10px]">
                                NEW
                              </span>
                            ) : (
                              <span className="bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded text-[10px]">
                                {it.training_status}
                              </span>
                            )}
                          </td>
                          <td className="text-center">
                            <button
                              onClick={() => handleDeleteItem(it.sr_no)}
                              className="text-red-500 hover:text-red-700 hover:bg-red-100 p-1 rounded transition"
                              title={isDwgMissing ? "Delete item with missing drawing number from BOM" : "Delete item from BOM"}
                            >
                              <Trash2 className="w-3.5 h-3.5 inline" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-100 p-3 px-4 border-t border-gray-300 flex justify-between items-center">
          <div className="text-xs">
            {hasMissingDwg && (
              <span className="text-red-600 font-semibold flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5 inline mr-1 text-red-500" />
                <span>Delete or fix {missingDwgItems.length} item(s) without drawing number before saving</span>
              </span>
            )}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 border border-gray-400 bg-white rounded text-xs font-semibold text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            {preview && (
              <button
                onClick={handleCommit}
                disabled={isLoading || hasMissingDwg || previewItems.length === 0}
                className={`px-4 py-1.5 rounded text-xs font-bold flex items-center space-x-1.5 shadow transition ${
                  hasMissingDwg || previewItems.length === 0
                    ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                    : 'bg-[#107C41] hover:bg-[#0E6A38] text-white'
                }`}
                title={hasMissingDwg ? "Please delete items with missing drawing numbers or provide drawing numbers first" : "Save & Register BOM Recipe"}
              >
                <Save className="w-4 h-4" />
                <span>Save & Register BOM Recipe</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
