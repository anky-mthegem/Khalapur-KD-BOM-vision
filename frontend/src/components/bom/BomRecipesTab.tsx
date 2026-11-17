import React, { useState, useEffect } from 'react';
import { BomRecipe, PartCatalogItem } from '../../types/bom';
import { api } from '../../services/api';
import { Play, FileSpreadsheet, Layers, RefreshCw, CheckCircle2, AlertCircle, Download } from 'lucide-react';

interface BomRecipesTabProps {
  onLoadRecipe: (masterCode: string) => void;
  activeMasterCode: string;
}

export const BomRecipesTab: React.FC<BomRecipesTabProps> = ({
  onLoadRecipe,
  activeMasterCode
}) => {
  const [recipes, setRecipes] = useState<BomRecipe[]>([]);
  const [parts, setParts] = useState<PartCatalogItem[]>([]);
  const [subTab, setSubTab] = useState<'recipes' | 'parts'>('recipes');
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [recipesData, partsData] = await Promise.all([
        api.listRecipes(),
        api.listParts()
      ]);
      setRecipes(recipesData);
      setParts(partsData);
    } catch (e) {
      console.error("Error loading recipes/parts:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="flex-1 bg-white flex flex-col overflow-hidden text-xs select-none">
      {/* Sub-header navigation */}
      <div className="bg-[#F3F2F1] border-b border-[#D2D0CE] px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSubTab('recipes')}
            className={`px-3 py-1 rounded font-semibold transition ${subTab === 'recipes' ? 'bg-[#2B579A] text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
          >
            BOM Recipes ({recipes.length})
          </button>
          <button
            onClick={() => setSubTab('parts')}
            className={`px-3 py-1 rounded font-semibold transition ${subTab === 'parts' ? 'bg-[#2B579A] text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
          >
            Global Parts Catalog ({parts.length})
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href="/api/bom/download-template"
            download="Standard_Plant_BOM_Template.xlsx"
            className="flex items-center space-x-1.5 px-3 py-1 bg-[#107C41] hover:bg-[#0E6032] text-white rounded font-semibold transition shadow-sm"
            title="Download plant standard Excel BOM template"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Standard Template (.xlsx)</span>
          </a>

          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center space-x-1 px-2.5 py-1 bg-white border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {subTab === 'recipes' && (
          <div className="space-y-3">
            <h3 className="font-bold text-gray-800 text-sm">Manufacturing Assembly Recipes</h3>
            <div className="border border-gray-300 rounded overflow-hidden">
              <table className="excel-grid-table">
                <thead>
                  <tr>
                    <th className="w-12 text-center">ID</th>
                    <th className="w-48">Master Item Code</th>
                    <th>Description</th>
                    <th className="w-24 text-center">Total Items</th>
                    <th className="w-24 text-center">Vision Inspected</th>
                    <th className="w-28 text-center">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {recipes.map((r) => {
                    const isActive = r.master_item_code === activeMasterCode;
                    return (
                      <tr key={r.id} className={isActive ? 'bg-blue-50/70 font-semibold' : 'hover:bg-gray-50'}>
                        <td className="text-center font-mono text-gray-500">{r.id}</td>
                        <td className="font-mono text-[#2B579A] font-bold">{r.master_item_code}</td>
                        <td className="text-gray-800">{r.description}</td>
                        <td className="text-center font-mono">{r.total_items}</td>
                        <td className="text-center font-mono text-[#107C10] font-bold">{r.vision_items_count}</td>
                        <td className="text-center">
                          {isActive ? (
                            <span className="badge-pass">ACTIVE NOW</span>
                          ) : (
                            <button
                              onClick={() => onLoadRecipe(r.master_item_code)}
                              className="px-2.5 py-0.5 bg-[#2B579A] hover:bg-[#1E3E6D] text-white rounded text-[11px] font-semibold inline-flex items-center space-x-1"
                            >
                              <Play className="w-3 h-3 fill-white" />
                              <span>Load Kit</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {subTab === 'parts' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-gray-800 text-sm">Global Parts Master & YOLO Class Index</h3>
                <p className="text-gray-500 text-[11px]">
                  Maintains persistent, contiguous YOLO26 class indices (0..N-1) for dataset annotation and training.
                </p>
              </div>
            </div>

            <div className="border border-gray-300 rounded overflow-hidden">
              <table className="excel-grid-table">
                <thead>
                  <tr>
                    <th className="w-16 text-center">YOLO ID</th>
                    <th className="w-56">Canonical Part UID</th>
                    <th>Item Description</th>
                    <th className="w-28">Drawing No</th>
                    <th className="w-24 text-center">Training Status</th>
                    <th className="w-20 text-center">Samples</th>
                  </tr>
                </thead>
                <tbody>
                  {parts.map((p) => {
                    const statusClass =
                      p.training_status === 'TRAINED'
                        ? 'bg-green-100 text-green-800'
                        : p.training_status === 'LABELED'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800';

                    return (
                      <tr key={p.id} className="hover:bg-gray-50">
                        <td className="text-center font-mono font-bold text-gray-700 bg-gray-50">{p.yolo_class_id}</td>
                        <td className="font-mono text-blue-800 font-semibold">{p.part_uid}</td>
                        <td>{p.item_name}</td>
                        <td className="font-mono text-gray-600">{p.drawing_no || "—"}</td>
                        <td className="text-center">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${statusClass}`}>
                            {p.training_status}
                          </span>
                        </td>
                        <td className="text-center font-mono font-bold">{p.sample_count}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
