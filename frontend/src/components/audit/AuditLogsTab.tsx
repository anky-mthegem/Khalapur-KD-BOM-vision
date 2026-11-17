import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { AuditSessionLog } from '../../types/bom';
import { RefreshCw, CheckCircle2, AlertOctagon, Image as ImageIcon } from 'lucide-react';

export const AuditLogsTab: React.FC = () => {
  const [logs, setLogs] = useState<AuditSessionLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSnapshot, setSelectedSnapshot] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs(50);
      setLogs(data);
    } catch (e) {
      console.error("Audit logs fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="flex-1 bg-white p-6 overflow-y-auto text-xs select-none">
      <div className="max-w-5xl mx-auto space-y-4">
        {/* Header */}
        <div className="border-b border-gray-200 pb-3 flex justify-between items-center">
          <div>
            <h2 className="text-base font-bold text-gray-800">Manufacturing Quality & Inspection Audit Logs</h2>
            <p className="text-gray-500 text-xs">
              Complete chronological audit trail of verified hardware packaging batches and camera snapshots.
            </p>
          </div>
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="flex items-center space-x-1 px-3 py-1 bg-gray-100 hover:bg-gray-200 border rounded text-gray-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Logs</span>
          </button>
        </div>

        {/* Logs Table */}
        <div className="border border-gray-300 rounded overflow-hidden">
          <table className="excel-grid-table">
            <thead>
              <tr>
                <th className="w-12 text-center">#</th>
                <th className="w-48">Batch UID</th>
                <th className="w-40">Master Item Code</th>
                <th className="w-36">Timestamp</th>
                <th className="w-24 text-center">Target Pcs</th>
                <th className="w-24 text-center">Counted Pcs</th>
                <th className="w-28 text-center">QC Status</th>
                <th className="w-24 text-center">Snapshot</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const isPassed = log.status === 'PASSED';
                return (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="text-center font-mono text-gray-500">{log.id}</td>
                    <td className="font-mono text-gray-700 truncate" title={log.session_uid}>
                      {log.session_uid.slice(0, 8)}...
                    </td>
                    <td className="font-mono font-bold text-[#2B579A]">{log.master_item_code}</td>
                    <td className="text-gray-600 font-mono text-[11px]">
                      {log.start_time ? new Date(log.start_time).toLocaleString() : "—"}
                    </td>
                    <td className="text-center font-mono font-bold">{log.total_target}</td>
                    <td className="text-center font-mono font-bold text-sm">{log.total_counted}</td>
                    <td className="text-center">
                      {isPassed ? (
                        <span className="badge-pass">
                          <CheckCircle2 className="w-3 h-3 mr-0.5" /> PASSED
                        </span>
                      ) : (
                        <span className="badge-fail">
                          <AlertOctagon className="w-3 h-3 mr-0.5" /> BLOCKED
                        </span>
                      )}
                    </td>
                    <td className="text-center">
                      {log.snapshot_path ? (
                        <button
                          onClick={() => setSelectedSnapshot(log.snapshot_path)}
                          className="px-2 py-0.5 bg-blue-100 hover:bg-blue-200 text-[#2B579A] rounded text-[10px] font-bold inline-flex items-center space-x-1"
                        >
                          <ImageIcon className="w-3 h-3" />
                          <span>View</span>
                        </button>
                      ) : (
                        <span className="text-gray-400 italic">None</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center py-6 text-gray-500 italic">
                    No inspection batches completed yet. Run inspection on the Home tab.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Snapshot Modal Preview */}
        {selectedSnapshot && (
          <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={() => setSelectedSnapshot(null)}>
            <div className="bg-white p-3 rounded-lg max-w-2xl w-full shadow-2xl space-y-2" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center border-b pb-2">
                <span className="font-bold text-gray-800 text-sm">Batch QC Audit Snapshot</span>
                <button onClick={() => setSelectedSnapshot(null)} className="text-gray-500 hover:text-black font-bold">✕</button>
              </div>
              <img src={selectedSnapshot} alt="Audit Snapshot" className="w-full rounded border" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
