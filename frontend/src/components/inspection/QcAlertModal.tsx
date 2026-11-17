import React from 'react';
import { AlertOctagon, CheckCircle2, Printer, X, ShieldAlert } from 'lucide-react';
import { QcVerificationResult } from '../../types/bom';

interface QcAlertModalProps {
  result: QcVerificationResult | null;
  onClose: () => void;
  onPrintLabel: () => void;
}

export const QcAlertModal: React.FC<QcAlertModalProps> = ({
  result,
  onClose,
  onPrintLabel
}) => {
  if (!result) return null;

  const isPassed = result.status === 'PASSED';

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 select-none">
      <div className="bg-white rounded-lg shadow-2xl max-w-lg w-full overflow-hidden border border-gray-300 animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className={`${isPassed ? 'bg-[#107C10]' : 'bg-[#D13438]'} text-white p-4 flex items-center justify-between`}>
          <div className="flex items-center space-x-2">
            {isPassed ? <CheckCircle2 className="w-6 h-6" /> : <AlertOctagon className="w-6 h-6 animate-pulse" />}
            <div>
              <h3 className="font-bold text-base leading-tight">
                {isPassed ? "QC VERIFICATION PASSED (100% MATCH)" : "BATCH BLOCKED: BOM VERIFICATION FAILED"}
              </h3>
              <p className="text-xs text-white/80">
                {isPassed ? "All kit fasteners and hardware counted accurately." : "Hardware kit count discrepancy detected. Label printing blocked."}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-4 space-y-3 text-xs">
          {/* Summary Box */}
          <div className="bg-gray-50 p-2.5 rounded border border-gray-200 flex justify-between font-mono">
            <div>
              <span className="text-gray-500">Target Pieces:</span> <strong>{result.total_target}</strong>
            </div>
            <div>
              <span className="text-gray-500">Counted Pieces:</span> <strong>{result.total_counted}</strong>
            </div>
            {result.qc_token && (
              <div>
                <span className="text-gray-500">QC Token:</span> <strong className="text-[#107C10]">{result.qc_token}</strong>
              </div>
            )}
          </div>

          {/* Missing Items List (Red Alert) */}
          {result.missing_items.length > 0 && (
            <div className="border border-red-200 bg-red-50/60 rounded p-3">
              <div className="flex items-center space-x-1 text-[#D13438] font-bold mb-2">
                <ShieldAlert className="w-4 h-4" />
                <span>MISSING HARDWARE ITEMS ({result.missing_items.length}):</span>
              </div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {result.missing_items.map((m, idx) => (
                  <div key={idx} className="bg-white p-2 rounded border border-red-200 flex items-center justify-between">
                    <div>
                      <span className="font-mono font-bold text-red-800">{m.drawing_no}</span>
                      <p className="text-[11px] text-gray-700 truncate max-w-xs">{m.item_name}</p>
                    </div>
                    <div className="text-right font-mono">
                      <span className="bg-red-100 text-[#D13438] px-2 py-0.5 rounded font-bold">
                        MISSING -{m.missing_qty}
                      </span>
                      <p className="text-[10px] text-gray-500 mt-0.5">Count: {m.counted_qty} / {m.target_qty}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Overcounted Items List */}
          {result.overcounted_items.length > 0 && (
            <div className="border border-yellow-200 bg-yellow-50/60 rounded p-3">
              <span className="text-yellow-800 font-bold mb-2 block">OVER-COUNTED ITEMS:</span>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {result.overcounted_items.map((o, idx) => (
                  <div key={idx} className="bg-white p-1.5 rounded border border-yellow-200 flex justify-between">
                    <span className="font-mono text-gray-800">{o.drawing_no} ({o.item_name})</span>
                    <span className="font-bold text-yellow-700">+{o.over_qty} pcs</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Audit Snapshot Thumbnail */}
          {result.snapshot_url && (
            <div>
              <span className="text-gray-500 font-semibold block mb-1">Audit Verification Snapshot:</span>
              <img
                src={result.snapshot_url}
                alt="Audit Snapshot"
                className="w-full h-32 object-cover rounded border border-gray-300"
              />
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="bg-gray-100 px-4 py-3 border-t border-gray-300 flex justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-3 py-1.5 border border-gray-400 bg-white rounded text-xs font-semibold text-gray-700 hover:bg-gray-50"
          >
            Close
          </button>
          {isPassed && (
            <button
              onClick={() => {
                onPrintLabel();
                onClose();
              }}
              className="px-4 py-1.5 bg-[#107C10] hover:bg-[#0E6A0E] text-white rounded text-xs font-bold flex items-center space-x-1 shadow"
            >
              <Printer className="w-4 h-4" />
              <span>Print QC Label</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
