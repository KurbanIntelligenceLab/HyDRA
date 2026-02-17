import { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, XCircle, Plus, Loader2 } from 'lucide-react';
import { createProject, uploadCsv, uploadXyz } from '../api';
import { MathNotation } from '../utils/mathNotation';

export default function DataUpload({ projects, onProjectCreated }) {
  const [projectName, setProjectName] = useState('');
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState(null);
  const [csvResult, setCsvResult] = useState(null);
  const [xyzResults, setXyzResults] = useState([]);
  const [error, setError] = useState(null);
  const csvRef = useRef(null);
  const xyzRef = useRef(null);

  const handleCreate = async () => {
    if (!projectName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const result = await createProject(projectName);
      setCreated(result);
      onProjectCreated?.();
    } catch (err) {
      setError(err.message);
    }
    setCreating(false);
  };

  const handleCsvUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !created) return;
    setError(null);
    try {
      const result = await uploadCsv(created.name, file);
      setCsvResult(result);
      onProjectCreated?.();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleXyzUpload = async (e) => {
    const files = e.target.files;
    if (!files || !created) return;
    setError(null);
    const results = [];
    for (const file of files) {
      try {
        const result = await uploadXyz(created.name, file);
        results.push({ file: file.name, ...result });
      } catch (err) {
        results.push({ file: file.name, error: err.message });
      }
    }
    setXyzResults(results);
    onProjectCreated?.();
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Step 1: Create project */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
          <Plus className="w-5 h-5 text-blue-600" />
          Step 1: Create New Project
        </h2>
        <p className="text-sm text-slate-500 mb-4">
          Upload your own materials data to analyze with the multi-agent system.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Project name (e.g., my-materials)"
            className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={!!created}
          />
          <button
            onClick={handleCreate}
            disabled={!projectName.trim() || creating || !!created}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create'}
          </button>
        </div>
        {created && (
          <div className="flex items-center gap-2 mt-3 text-green-600 text-sm">
            <CheckCircle2 className="w-4 h-4" />
            Project "{created.name}" created
          </div>
        )}
      </div>

      {/* Step 2: Upload CSV */}
      {created && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-600" />
            Step 2: Upload Descriptor CSV
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            CSV must have a <code className="bg-slate-100 px-1 rounded text-xs">system_label</code> column
            and numeric descriptor columns. Optional: <code className="bg-slate-100 px-1 rounded text-xs">E_ads_eV</code> (<MathNotation.Eads /> in eV) for ML analysis.
          </p>
          <div
            onClick={() => csvRef.current?.click()}
            className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-colors"
          >
            <Upload className="w-8 h-8 mx-auto text-slate-400 mb-2" />
            <p className="text-sm text-slate-500">Click or drag to upload CSV file</p>
          </div>
          <input ref={csvRef} type="file" accept=".csv" onChange={handleCsvUpload} className="hidden" />
          {csvResult && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-green-700 font-medium text-sm mb-2">
                <CheckCircle2 className="w-4 h-4" />
                CSV uploaded successfully
              </div>
              <div className="text-xs text-green-600 space-y-1">
                <div>Systems: {csvResult.validation?.system_labels?.join(', ')}</div>
                <div>Columns: {csvResult.validation?.numeric_columns?.length} numeric descriptors</div>
                <div>Has <MathNotation.Eads />: {csvResult.validation?.has_adsorption_energy ? 'Yes' : 'No'}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Step 3: Upload XYZ */}
      {created && csvResult && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <Upload className="w-5 h-5 text-green-600" />
            Step 3: Upload XYZ Geometry Files (Optional)
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            Standard XYZ format. Optional 4th column for Mulliken charges.
            File names should match system labels (e.g., <code className="bg-slate-100 px-1 rounded text-xs">1Zr-TiO2.xyz</code>).
          </p>
          <div
            onClick={() => xyzRef.current?.click()}
            className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center cursor-pointer hover:border-green-400 hover:bg-green-50/50 transition-colors"
          >
            <Upload className="w-8 h-8 mx-auto text-slate-400 mb-2" />
            <p className="text-sm text-slate-500">Click to upload XYZ files (multiple allowed)</p>
          </div>
          <input ref={xyzRef} type="file" accept=".xyz" multiple onChange={handleXyzUpload} className="hidden" />
          {xyzResults.length > 0 && (
            <div className="mt-4 space-y-2">
              {xyzResults.map((r, i) => (
                <div key={i} className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg ${
                  r.error ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'
                }`}>
                  {r.error ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                  {r.file}: {r.error || `${r.validation?.num_atoms} atoms`}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-2 text-red-700 text-sm">
          <XCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Existing projects */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Existing Projects</h3>
        <div className="space-y-2">
          {projects.map((p) => (
            <div key={p.name} className="flex items-center justify-between bg-slate-50 rounded-lg p-3">
              <div>
                <span className="font-medium text-sm text-slate-700">{p.name}</span>
                {p.builtin && <span className="ml-2 text-[10px] bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">built-in</span>}
              </div>
              <div className="text-xs text-slate-500">
                {p.systems?.length || 0} systems | {p.num_xyz || 0} structures | CSV: {p.has_csv ? 'Yes' : 'No'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
