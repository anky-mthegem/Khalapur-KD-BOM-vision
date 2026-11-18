import React from 'react';
import { InspectionItemStatus } from '../../types/bom';
import { Eye, EyeOff, Check, Clock, AlertCircle } from 'lucide-react';

interface BomGridProps {
  items: InspectionItemStatus[];
  onToggleVisionInspected: (itemId: number) => void;
  masterItemCode: string | null;
}

export const BomGrid: React.FC<BomGridProps> = ({
  items,
  onToggleVisionInspected,
  masterItemCode
}) => {
  const totalTarget = items.reduce((acc, it) => acc + (it.is_vision_inspected ? it.target_qty : 0), 0);
  const totalCounted = items.reduce((acc, it) => acc + (it.is_vision_inspected ? it.counted_qty : 0), 0);
  const totalBalance = Math.max(0, totalTarget - totalCounted);

  const getRowClass = (item: InspectionItemStatus) => {
    if (!item.is_vision_inspected) {
      return 'bg-[#EDEBE9] text-gray-500 italic';
    }
    switch (item.status) {
      case 'MATCH':
        return 'bg-[#DFF6DD] text-[#107C10] font-medium';
      case 'IN_PROGRESS':
        return 'bg-[#FFF4CE] text-[#7A6000]';
      case 'OVERCOUNT':
        return 'bg-[#FDE7E9] text-[#D13438] font-bold';
      default:
        return 'bg-white hover:bg-blue-50/50';
    }
  };

  const getStatusBadge = (item: InspectionItemStatus) => {
    if (!item.is_vision_inspected) {
      return (
        <span className="badge-excluded">
          <EyeOff className="w-3 h-3 mr-1" />
          EXCL
        </span>
      );
    }
    switch (item.status) {
      case 'MATCH':
        return (
          <span className="badge-pass">
            <Check className="w-3 h-3 mr-0.5" />
            MATCH
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="badge-progress">
            <Clock className="w-3 h-3 mr-0.5" />
            PROG
          </span>
        );
      case 'OVERCOUNT':
        return (
          <span className="badge-fail">
            <AlertCircle className="w-3 h-3 mr-0.5" />
            OVER
          </span>
        );
      default:
        return (
          <span className="badge-pending">
            WAIT
          </span>
        );
    }
  };

  return (
    <div className="w-[420px] 2xl:w-[480px] bg-white flex flex-col h-full border-l border-[#D2D0CE] select-none text-xs">
      {/* Grid Title Bar */}
      <div className="bg-[#F3F2F1] px-3 py-2 border-b border-[#D2D0CE] flex items-center justify-between">
        <div>
          <span className="font-bold text-gray-800 uppercase tracking-wide">BOM Recipe Items</span>
          <span className="text-[11px] text-gray-500 ml-1">({items.length} lines)</span>
        </div>
        <div className="font-mono text-[11px] bg-white px-2 py-0.5 rounded border border-gray-300 font-semibold text-[#2B579A]">
          {masterItemCode || "DEFAULT"}
        </div>
      </div>

      {/* Excel Table Container */}
      <div className="flex-1 overflow-y-auto">
        <table className="excel-grid-table">
          <thead className="sticky top-0 shadow-sm z-10">
            <tr>
              <th className="w-8 text-center">#</th>
              <th>Item Name</th>
              <th className="w-20">Drawing No</th>
              <th className="w-10 text-center">Tgt</th>
              <th className="w-10 text-center">Cnt</th>
              <th className="w-8 text-center" title="Vision Inspected Flag">Vis</th>
              <th className="w-14 text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.sr_no} className={`${getRowClass(it)} transition-colors`}>
                <td className="text-center font-mono text-gray-500 font-bold">{it.sr_no}</td>
                <td className="truncate max-w-[140px] 2xl:max-w-[180px]" title={it.item_name}>
                  {it.item_name}
                </td>
                <td className="font-mono text-[11px] text-gray-700 truncate" title={it.drawing_no}>
                  {it.drawing_no}
                </td>
                <td className="text-center font-mono font-bold">{it.target_qty}</td>
                <td className="text-center font-mono font-bold text-sm">
                  {it.counted_qty}
                </td>
                <td className="text-center">
                  <input
                    type="checkbox"
                    checked={it.is_vision_inspected}
                    onChange={() => onToggleVisionInspected(it.id ?? it.sr_no)}
                    className="cursor-pointer rounded text-[#2B579A]"
                    title={it.is_vision_inspected ? "Vision Active" : "Excluded from Vision Gate"}
                  />
                </td>
                <td className="text-center">
                  {getStatusBadge(it)}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-6 text-gray-500 italic">
                  No recipe items loaded. Scan a Master Code or Import an Excel BOM.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="bg-[#F3F2F1] p-2.5 border-t border-[#D2D0CE] flex items-center justify-between text-xs font-mono">
        <div>
          <span className="text-gray-500">Target:</span> <strong className="text-gray-800">{totalTarget}</strong>
          <span className="text-gray-400 mx-1.5">|</span>
          <span className="text-gray-500">Counted:</span> <strong className="text-[#107C10] text-sm">{totalCounted}</strong>
        </div>
        <div>
          <span className="text-gray-500">Balance:</span> <strong className="text-[#D13438] text-sm">{totalBalance}</strong>
        </div>
      </div>
    </div>
  );
};
