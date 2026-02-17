import { useState, useEffect, useRef } from 'react';
import { Atom, ChevronDown } from 'lucide-react';
import { getStructures, getStructure } from '../api';

export default function MoleculeViewer({ project }) {
  const [structures, setStructures] = useState([]);
  const [selected, setSelected] = useState(null);
  const [vizData, setVizData] = useState(null);
  const [colorBy, setColorBy] = useState('element');
  const [loading, setLoading] = useState(false);
  const viewerRef = useRef(null);
  const viewerInstance = useRef(null);

  useEffect(() => {
    getStructures(project).then((data) => {
      setStructures(data);
      if (data.length > 0 && !selected) setSelected(data[0].system_label);
    }).catch(() => {});
  }, [project]);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    getStructure(project, selected).then((data) => {
      setVizData(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [selected, project]);

  useEffect(() => {
    if (!vizData || !viewerRef.current) return;

    // Initialize 3Dmol viewer
    if (typeof window.$3Dmol !== 'undefined') {
      if (viewerInstance.current) {
        viewerInstance.current.clear();
      } else {
        viewerInstance.current = window.$3Dmol.createViewer(viewerRef.current, {
          backgroundColor: '#f8fafc',
        });
      }

      const viewer = viewerInstance.current;
      viewer.addModel(vizData.xyz_text, 'xyz');

      if (colorBy === 'charge' && vizData.has_charges) {
        const atoms = viewer.getModel().selectedAtoms({});
        for (let i = 0; i < atoms.length && i < vizData.atoms.length; i++) {
          const cn = vizData.atoms[i].charge_normalized;
          if (cn !== undefined) {
            // Blue (low charge) → Red (high charge)
            const r = Math.round(cn * 255);
            const b = Math.round((1 - cn) * 255);
            const color = `rgb(${r},50,${b})`;
            atoms[i].color = color;
          }
        }
        viewer.setStyle({}, { sphere: { scale: 0.3, colorscheme: { prop: 'color' } } });
      } else {
        viewer.setStyle({}, {
          sphere: {
            scale: 0.3,
            colorscheme: {
              prop: 'elem',
              map: { Ti: '#73C2FB', O: '#FF0D0D', Zr: '#00CC00', H: '#FFFFFF' },
            },
          },
        });
      }

      viewer.zoomTo();
      viewer.render();
    }
  }, [vizData, colorBy]);

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Atom className="w-5 h-5 text-blue-600" />
            3D Structure Viewer
          </h2>
          <div className="flex gap-2">
            <select
              value={selected || ''}
              onChange={(e) => setSelected(e.target.value)}
              className="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5"
            >
              {structures.map((s) => (
                <option key={s.system_label} value={s.system_label}>
                  {s.system_label}
                </option>
              ))}
            </select>
            <select
              value={colorBy}
              onChange={(e) => setColorBy(e.target.value)}
              className="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5"
            >
              <option value="element">Color by Element</option>
              <option value="charge">Color by Mulliken Charge</option>
            </select>
          </div>
        </div>

        {/* 3Dmol viewer container */}
        <div className="relative bg-slate-50 rounded-lg overflow-hidden" style={{ height: '500px' }}>
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-50/80 z-10">
              <span className="text-sm text-slate-500">Loading structure...</span>
            </div>
          )}
          <div ref={viewerRef} style={{ width: '100%', height: '100%' }} />
          {!vizData && !loading && (
            <div className="absolute inset-0 flex items-center justify-center text-slate-400">
              <div className="text-center">
                <Atom className="w-12 h-12 mx-auto mb-2" />
                <p className="text-sm">Select a structure to view</p>
                <p className="text-xs mt-1">
                  Tip: Include the 3Dmol.js script in index.html for interactive 3D
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Structure info */}
        {vizData && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-50 rounded-lg p-3">
              <div className="text-xs text-slate-500">Atoms</div>
              <div className="text-lg font-bold text-slate-800">{vizData.num_atoms}</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <div className="text-xs text-slate-500">Elements</div>
              <div className="text-lg font-bold text-slate-800">{vizData.elements.join(', ')}</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <div className="text-xs text-slate-500">Charges</div>
              <div className="text-lg font-bold text-slate-800">{vizData.has_charges ? 'Yes' : 'No'}</div>
            </div>
            {vizData.charge_range && (
              <div className="bg-slate-50 rounded-lg p-3">
                <div className="text-xs text-slate-500">Charge Range</div>
                <div className="text-sm font-bold text-slate-800">
                  {vizData.charge_range.min.toFixed(2)} to {vizData.charge_range.max.toFixed(2)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Element legend */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <h3 className="text-sm font-medium text-slate-600 mb-2">Element Legend</h3>
        <div className="flex gap-4">
          {[
            { el: 'Ti', color: '#73C2FB', label: 'Titanium' },
            { el: 'O', color: '#FF0D0D', label: 'Oxygen' },
            { el: 'Zr', color: '#00CC00', label: 'Zirconium' },
            { el: 'H', color: '#CCCCCC', label: 'Hydrogen' },
          ].map(({ el, color, label }) => (
            <div key={el} className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full border border-slate-200" style={{ backgroundColor: color }} />
              <span className="text-xs text-slate-600">{label} ({el})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
