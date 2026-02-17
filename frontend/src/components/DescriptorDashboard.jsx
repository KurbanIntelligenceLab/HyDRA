import { useState, useEffect } from 'react';
import { Database, Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getDescriptors, getCorrelation, getShifts } from '../api';
import PublicationFigures from './PublicationFigures';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];

// Format descriptor names for display
function formatDescriptorName(name) {
  if (!name) return name;

  // Handle special cases
  const specialCases = {
    'system_label': 'System',
    'E_ads_eV': 'E_ads (eV)',
    'E_ads': 'E_ads (eV)',
    'HOMO_eV': 'HOMO (eV)',
    'LUMO_eV': 'LUMO (eV)',
    'Eg_eV': 'E_g (eV)',
    'IP_eV': 'IP (eV)',
    'EA_eV': 'EA (eV)',
    'mu_eV': 'μ (eV)',
    'chi_eV': 'χ (eV)',
    'eta_eV': 'η (eV)',
    'S_eV_inv': 'S (eV⁻¹)',
    'omega_eV': 'ω (eV)',
    'deltaN_max': 'ΔN_max',
    'E_surface_eV': 'E_surface (eV)',
    'E_surface+H2_eV': 'E_surface+H₂ (eV)',
    'E_H2_eV': 'E_H₂ (eV)',
  };

  if (specialCases[name]) return specialCases[name];

  // Generic pattern: replace _eV with (eV), _K with (K), etc.
  let formatted = name
    .replace(/_eV$/, ' (eV)')
    .replace(/_K$/, ' (K)')
    .replace(/_bar$/, ' (bar)')
    .replace(/_inv$/, '⁻¹')
    .replace(/delta/gi, 'Δ')
    .replace(/_/g, ' ');

  return formatted;
}

export default function DescriptorDashboard({ project }) {
  const [data, setData] = useState(null);
  const [correlation, setCorrelation] = useState(null);
  const [shifts, setShifts] = useState(null);
  const [selectedDescriptor, setSelectedDescriptor] = useState('Eg_eV');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('[DescriptorDashboard] Loading data for project:', project);
    setLoading(true);
    setError(null);

    Promise.all([
      getDescriptors(project),
      getCorrelation(project),
      getShifts(project),
    ]).then(([desc, corr, sh]) => {
      console.log('[DescriptorDashboard] Data loaded:', { desc, corr, sh });
      setData(desc);
      setCorrelation(corr);
      setShifts(sh);

      if (desc?.summary?.descriptors?.length > 0) {
        setSelectedDescriptor(desc.summary.descriptors[0]);
      }

      setLoading(false);
    }).catch((err) => {
      console.error('[DescriptorDashboard] Error loading data:', err);
      setError(err.message || String(err) || 'Failed to load data');
      setLoading(false);
    });
  }, [project]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-2" />
        <span className="text-slate-500">Loading descriptors...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-red-200 p-6">
        <div className="text-center py-12">
          <div className="text-red-500 font-semibold mb-2">Error Loading Descriptors</div>
          <div className="text-slate-600 text-sm">{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-slate-700 font-medium text-center py-20">No data available for this project</div>
    );
  }

  const summary = data?.summary || {};
  const descriptors = summary?.descriptors || [];

  // Bar chart data for selected descriptor
  const barData = (data?.data || []).map((row) => ({
    name: row.system_label,
    value: parseFloat(row[selectedDescriptor]) || 0,
  }));

  // Correlation heatmap data
  const corrData = [];
  if (correlation) {
    const { columns, matrix } = correlation;
    for (let i = 0; i < columns.length; i++) {
      for (let j = 0; j < columns.length; j++) {
        corrData.push({ x: columns[j], y: columns[i], value: matrix[i][j] });
      }
    }
  }

  // Shift heatmap
  const shiftRows = [];
  if (shifts?.shifts) {
    for (const [system, shiftMap] of Object.entries(shifts.shifts)) {
      const row = { system };
      for (const [desc, val] of Object.entries(shiftMap)) {
        row[desc] = val;
      }
      shiftRows.push(row);
    }
  }

  return (
    <div className="space-y-6">
      {/* Publication Figures Mega-Panel */}
      <PublicationFigures project={project} />

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="text-xs text-slate-500">Systems</div>
          <div className="text-2xl font-bold text-blue-600">{summary?.num_systems || 0}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="text-xs text-slate-500">Descriptors</div>
          <div className="text-2xl font-bold text-purple-600">{summary?.num_descriptors || 0}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="text-xs text-slate-500">Adsorption Pairs</div>
          <div className="text-2xl font-bold text-green-600">{shifts?.pairs_found || 0}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="text-xs text-slate-500">Project</div>
          <div className="text-lg font-bold text-slate-700 truncate">{project}</div>
        </div>
      </div>

      {/* Descriptor comparison chart */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Descriptor Comparison
          </h2>
          <select
            value={selectedDescriptor}
            onChange={(e) => setSelectedDescriptor(e.target.value)}
            className="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5"
          >
            {descriptors.map((d) => (
              <option key={d} value={d}>{formatDescriptorName(d)}</option>
            ))}
          </select>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) : '—')} />
            <Tooltip formatter={(v) => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) : '—')} />
            <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} name={formatDescriptorName(selectedDescriptor)} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Correlation heatmap (simplified as a table) */}
      {correlation && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 overflow-x-auto">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Correlation Matrix</h2>
          <table className="text-xs w-full">
            <thead>
              <tr>
                <th className="p-1"></th>
                {correlation.columns.map((c) => (
                  <th key={c} className="p-1 text-slate-500 font-medium" style={{ writingMode: 'vertical-lr', maxWidth: 40 }}>
                    {formatDescriptorName(c)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {correlation.columns.map((row, i) => (
                <tr key={row}>
                  <td className="p-1 font-medium text-slate-600 whitespace-nowrap">{formatDescriptorName(row)}</td>
                  {correlation.matrix[i].map((val, j) => {
                    // Handle null values (constant columns have undefined correlation)
                    if (val === null || val === undefined || isNaN(val)) {
                      return (
                        <td key={j} className="p-1 text-center text-slate-300">
                          —
                        </td>
                      );
                    }
                    const absVal = Math.abs(val);
                    const color = val > 0
                      ? `rgba(59, 130, 246, ${absVal * 0.8})`
                      : `rgba(239, 68, 68, ${absVal * 0.8})`;
                    return (
                      <td
                        key={j}
                        className="p-1 text-center"
                        style={{ backgroundColor: color, color: absVal > 0.5 ? 'white' : 'inherit' }}
                        title={`${formatDescriptorName(row)} vs ${formatDescriptorName(correlation.columns[j])}: ${val.toFixed(3)}`}
                      >
                        {val.toFixed(2)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Descriptor shifts upon adsorption */}
      {shiftRows.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">
            Descriptor Shifts Upon Adsorption
          </h2>
          <div className="overflow-x-auto">
            <table className="text-xs w-full">
              <thead>
                <tr>
                  <th className="p-2 text-left text-slate-600">System</th>
                  {Object.keys(shiftRows[0]).filter(k => k !== 'system').map((d) => (
                    <th key={d} className="p-2 text-slate-500 font-medium">{formatDescriptorName(d)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {shiftRows.map((row) => (
                  <tr key={row.system} className="border-t border-slate-100">
                    <td className="p-2 font-medium text-slate-700">{row.system}</td>
                    {Object.entries(row).filter(([k]) => k !== 'system').map(([k, v]) => {
                      const absV = Math.abs(v);
                      const maxShift = 0.03;
                      const intensity = Math.min(absV / maxShift, 1);
                      const bg = v > 0
                        ? `rgba(34, 197, 94, ${intensity * 0.6})`
                        : `rgba(139, 92, 246, ${intensity * 0.6})`;
                      return (
                        <td key={k} className="p-2 text-center font-mono" style={{ backgroundColor: bg }}>
                          {typeof v === 'number' && !isNaN(v) ? v.toFixed(3) : '—'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Raw data table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 overflow-x-auto">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Full Dataset</h2>
        <table className="text-xs w-full">
          <thead>
            <tr>
              {data.columns.map((col) => (
                <th key={col} className="p-2 text-left text-slate-500 font-medium whitespace-nowrap">{formatDescriptorName(col)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.data.map((row, i) => (
              <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                {data.columns.map((col) => {
                  const val = row[col];
                  let displayVal = '—';
                  if (val !== null && val !== undefined) {
                    if (typeof val === 'number' && !isNaN(val)) {
                      displayVal = val.toFixed(3);
                    } else {
                      displayVal = String(val);
                    }
                  }
                  return (
                    <td key={col} className="p-2 font-mono whitespace-nowrap">
                      {displayVal}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
