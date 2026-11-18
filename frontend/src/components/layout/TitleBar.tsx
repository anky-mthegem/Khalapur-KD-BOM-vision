import React from 'react';
import { ShieldCheck, Factory, BookOpen } from 'lucide-react';

interface TitleBarProps {
  activeMasterCode: string;
  activeKitName?: string;
}

export const TitleBar: React.FC<TitleBarProps> = ({
  activeMasterCode,
  activeKitName
}) => {
  return (
    <div className="bg-[#2B579A] text-white h-9 px-3 flex items-center justify-between border-b border-[#1E3E6D] select-none text-xs">
      {/* Left: App Title */}
      <div className="flex items-center space-x-2 font-semibold tracking-wide flex-shrink-0">
        <Factory className="w-4 h-4 text-yellow-300" />
        <span className="font-bold text-sm">KD-BOM VISION INSPECTOR</span>
        <span className="text-blue-200">| Plant Line 1 (Khalapur)</span>
      </div>

      {/* Center: Active Recipe Badge with Code & Description */}
      <div className="flex items-center space-x-2 bg-[#1E3E6D] px-3 py-1 rounded border border-blue-400/40 max-w-[58%] min-w-0 shadow-sm mx-2">
        <span className="text-gray-300 text-[10px] uppercase tracking-wider font-semibold flex-shrink-0">Active Kit:</span>
        <span className="font-mono font-bold text-yellow-300 text-xs tracking-wide flex-shrink-0 bg-black/25 px-1.5 py-0.5 rounded border border-yellow-300/30">
          {activeMasterCode || "NO RECIPE LOADED"}
        </span>
        {activeKitName && (
          <span
            className="text-white text-xs font-semibold truncate border-l border-blue-400/40 pl-2 text-blue-50"
            title={activeKitName}
          >
            {activeKitName}
          </span>
        )}
      </div>

      {/* Right: Version and SOP Manual Link */}
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-1 text-blue-200 text-[11px]">
          <ShieldCheck className="w-3.5 h-3.5 text-green-400" />
          <span>v2.6.0-OBB</span>
        </div>

        <a
          href="/manual/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center space-x-1.5 bg-[#107C41] hover:bg-[#0E6032] text-white px-2.5 py-1 rounded border border-green-300/40 text-[11px] font-semibold transition-colors shadow-sm ml-2"
          title="Open Standard Operating Procedure (SOP) & Operator Manual"
        >
          <BookOpen className="w-3.5 h-3.5 text-yellow-300" />
          <span>SOP Manual</span>
        </a>
      </div>
    </div>
  );
};
