import React, { useState } from 'react';
import { Upload, X, Check, FileSpreadsheet, AlertTriangle, EyeOff, Save } from 'lucide-react';
import { api } from '../../services/api';
import { BomPreviewResponse } from '../../types/bom';

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
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState<BomPreviewResponse | null>(null);
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
      } catch (err: any) {
        setError(err.message || 'Failed to parse Excel spreadsheet');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleCommit = async () => {
    if (!preview) return;
    setIsLoading(true);
    try {
      await api.commitBom({
        master_item_code: preview.master_item_code,
        description: preview.description,
        items: preview.items.map((it) => ({
          sr_no: it.sr_no,
          part_uid: it.part_uid,
          item_name: it.item_name,
          drawing_no: it.drawing_no,
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
      <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden border border-gray-300">
        {/* Header */}
        <div className="bg-[#107C41] text-white p-3 px-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5" />
            <span className="font-bold text-sm">Import Manufacturing BOM Excel Spreadsheet</span>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 flex-1 overflow-y-auto space-y-4 text-xs">
          {/* File Selector */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50/50 transition">
            <input
              type="file"
              id="excel-upload-input"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="excel-upload-input" className="cursor-pointer flex flex-col items-center">
              <Upload className="w-8 h-8 text-[#107C41] mb-2" />
              <span className="font-bold text-gray-800 text-sm">
                {file ? file.name : "Click to select or drag & drop Plant BOM Excel file"}
              </span>
              <span className="text-[11px] text-gray-500 mt-1">
                Supports Microsoft Excel .xlsx and .xls (Auto-detects merged headers, drawings, and packaging items)
              </span>
            </label>
          </div>

          {isLoading && (
            <div className="text-center py-4 text-[#107C41] font-semibold animate-pulse">
              Parsing workbook, extracting merged headers, and slugging drawing numbers...
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
              <div className="bg-gray-50 p-3 rounded border border-gray-300 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Master Item Code:</span>{" "}
                  <strong className="font-mono text-[#2B579A] text-sm">{preview.master_item_code}</strong>
                </div>
                <div>
                  <span className="text-gray-500">Sheet:</span> <strong>{preview.sheet_name}</strong>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">Description:</span> <strong>{preview.description}</strong>
                </div>
                <div>
                  <span className="text-gray-500">Total Items:</span> <strong>{preview.total_items}</strong> (Vision: {preview.vision_items_count})
                </div>
                <div>
                  <span className="text-gray-500">Auto-Excluded Packaging:</span> <strong className="text-gray-600">{preview.excluded_packaging_count}</strong>
                </div>
              </div>

              {/* Table Preview */}
              <div className="border border-gray-300 rounded overflow-hidden max-h-64 overflow-y-auto">
                <table className="excel-grid-table">
                  <thead className="sticky top-0 bg-[#F3F2F1]">
                    <tr>
                      <th className="w-8 text-center">#</th>
                      <th>Item Name</th>
                      <th>Drawing No</th>
                      <th>Canonical Part UID</th>
                      <th className="w-10 text-center">Qty</th>
                      <th className="w-14 text-center">Vision</th>
                      <th className="w-16 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.items.map((it) => (
                      <tr key={it.sr_no} className={it.is_vision_inspected ? "bg-white" : "bg-gray-100 text-gray-500 italic"}>
                        <td className="text-center font-mono">{it.sr_no}</td>
                        <td className="truncate max-w-xs">{it.item_name}</td>
                        <td className="font-mono text-[11px]">{it.drawing_no}</td>
                        <td className="font-mono text-[11px] text-blue-700">{it.part_uid}</td>
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
                          {it.is_new_part ? (
                            <span className="bg-blue-100 text-blue-800 font-bold px-1.5 py-0.5 rounded text-[10px]">
                              NEW
                            </span>
                          ) : (
                            <span className="bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded text-[10px]">
                              {it.training_status}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-100 p-3 px-4 border-t border-gray-300 flex justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-3 py-1.5 border border-gray-400 bg-white rounded text-xs font-semibold text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          {preview && (
            <button
              onClick={handleCommit}
              disabled={isLoading}
              className="px-4 py-1.5 bg-[#107C41] hover:bg-[#0E6A38] text-white rounded text-xs font-bold flex items-center space-x-1.5 shadow"
            >
              <Save className="w-4 h-4" />
              <span>Save & Register BOM Recipe</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
