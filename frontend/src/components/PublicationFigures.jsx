import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import {
  ComposedChart, Bar, Scatter, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceArea,
} from 'recharts';
import {
  getAdsorptionEnergies, getEnergyDecomposition, getShifts,
  getT50, getCoverageP, getCoverageT,
} from '../api';

const SYS_COLORS = { Pristine: '#2ca02c', '1Zr': '#1f77b4', '2Zr': '#d62728' };

function systemColor(label) {
  if (/pristine/i.test(label)) return SYS_COLORS.Pristine;
  if (/2zr|zr2/i.test(label)) return SYS_COLORS['2Zr'];
  if (/1zr|zr/i.test(label)) return SYS_COLORS['1Zr'];
  return '#888';
}

function systemShort(label) {
  if (/pristine/i.test(label)) return 'Pristine';
  if (/2zr|zr2/i.test(label)) return '2Zr';
  if (/1zr|zr/i.test(label)) return '1Zr';
  return label;
}

const PANEL_LABEL = 'font-semibold text-slate-700 text-sm mb-1';

// ─── Panel (a): E_ads Lollipop ───
function PanelEadsLollipop({ eadsData }) {
  if (!eadsData?.found) return null;
  const order = ['Pristine', '1Zr', '2Zr'];
  const chartData = Object.entries(eadsData.data)
    .map(([label, val]) => ({ name: systemShort(label), value: val, color: systemColor(label) }))
    .sort((a, b) => order.indexOf(a.name) - order.indexOf(b.name));

  return (
    <div>
      <div className={PANEL_LABEL}>(a) Adsorption Energies</div>
      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(2) : '—')} label={{ value: 'E_ads (eV)', angle: -90, position: 'insideLeft', fontSize: 11, dx: -5 }} />
          <Tooltip formatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) + ' eV' : '—')} />
          <Bar dataKey="value" barSize={4} isAnimationActive={false}>
            {chartData.map((d, i) => (
              <rect key={i} fill={d.color} />
            ))}
          </Bar>
          <Scatter dataKey="value" isAnimationActive={false}>
            {chartData.map((d, i) => (
              <circle key={i} fill={d.color} r={5} />
            ))}
          </Scatter>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Panel (b): Energy Decomposition ───
function PanelEnergyDecomposition({ decompData }) {
  if (!decompData?.found) return null;
  const ref = decompData.reference;
  const systems = decompData.systems.filter(s => s.system !== ref);

  const chartData = systems.map(s => ({
    name: systemShort(s.system),
    elec: s.dE_elec_eV,
    rep: s.dE_rep_eV,
    disp: s.dE_disp_eV,
    total: s.dE_total_eV,
  }));

  return (
    <div>
      <div className={PANEL_LABEL}>(b) Energy Decomposition</div>
      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(2) : '—')} label={{ value: 'Shift vs pristine (eV)', angle: -90, position: 'insideLeft', fontSize: 11, dx: -5 }} />
          <Tooltip formatter={v => (typeof v === 'number' && !isNaN(v) ? (v >= 0 ? '+' : '') + v.toFixed(3) + ' eV' : '—')} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          <Bar dataKey="elec" stackId="a" fill="#1f77b4" name="ΔE_elec" />
          <Bar dataKey="rep" stackId="a" fill="#ff7f0e" name="ΔE_rep" />
          <Bar dataKey="disp" stackId="a" fill="#2ca02c" name="ΔE_disp" />
          <Scatter dataKey="total" fill="#d62728" name="ΔE_total" shape="circle" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Panel (c): Descriptor Shifts Heatmap ───
function PanelDescriptorShifts({ shiftsData }) {
  if (!shiftsData?.shifts || shiftsData.pairs_found === 0) return null;

  const descs = ['Eg_eV', 'mu_eV', 'omega_eV', 'chi_eV', 'eta_eV'];
  const descLabels = ['ΔEg', 'Δμ', 'Δω', 'Δχ', 'Δη'];
  const systems = Object.keys(shiftsData.shifts);
  const order = ['Pristine', '1Zr', '2Zr'];
  systems.sort((a, b) => {
    const ai = order.indexOf(systemShort(a));
    const bi = order.indexOf(systemShort(b));
    return ai - bi;
  });

  const values = systems.map(sys => descs.map(d => shiftsData.shifts[sys]?.[d] ?? 0));
  const allVals = values.flat().filter(v => v !== 0);
  const maxAbs = Math.max(...allVals.map(Math.abs), 0.001);

  function cellColor(v) {
    const intensity = Math.min(Math.abs(v) / maxAbs, 1) * 0.7;
    return v > 0
      ? `rgba(220, 38, 38, ${intensity})`
      : `rgba(37, 99, 235, ${intensity})`;
  }

  return (
    <div>
      <div className={PANEL_LABEL}>(c) Descriptor Shifts (H₂ uptake)</div>
      <div className="overflow-x-auto">
        <table className="text-xs w-full border-collapse">
          <thead>
            <tr>
              <th className="p-1.5 text-left text-slate-600">System</th>
              {descLabels.map(d => (
                <th key={d} className="p-1.5 text-center text-slate-600 font-medium">{d}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {systems.map((sys, i) => (
              <tr key={sys} className="border-t border-slate-100">
                <td className="p-1.5 font-medium text-slate-700 whitespace-nowrap">{systemShort(sys)}</td>
                {values[i].map((v, j) => (
                  <td key={j} className="p-1.5 text-center font-mono"
                    style={{ backgroundColor: cellColor(v), color: Math.abs(v) / maxAbs > 0.5 ? 'white' : 'inherit' }}>
                    {v.toFixed(4)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center gap-4 mt-2 text-[10px] text-slate-500">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(37,99,235,0.5)' }} /> Decrease
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(220,38,38,0.5)' }} /> Increase
        </div>
        <span>Units: eV</span>
      </div>
    </div>
  );
}

// ─── Panel (d): T50 vs Pressure ───
function PanelT50vsPressure({ t50Data }) {
  if (!t50Data || Object.keys(t50Data).length === 0) return null;

  const systems = Object.keys(t50Data);
  const order = ['Pristine', '1Zr', '2Zr'];
  systems.sort((a, b) => order.indexOf(systemShort(a)) - order.indexOf(systemShort(b)));

  // Merge all pressure points into unified chart data
  const pressureSet = new Set();
  systems.forEach(s => {
    const pressures = t50Data[s]?.pressures_bar;
    if (Array.isArray(pressures)) {
      pressures.forEach(p => pressureSet.add(p));
    }
  });
  const pressures = [...pressureSet].sort((a, b) => a - b);

  if (pressures.length === 0) return null;

  const chartData = pressures.map(p => {
    const point = { pressure: p };
    systems.forEach(s => {
      const sysData = t50Data[s];
      if (!sysData || !Array.isArray(sysData.pressures_bar) || !Array.isArray(sysData.T50_K)) return;

      const idx = sysData.pressures_bar.indexOf(p);
      if (idx >= 0 && idx < sysData.T50_K.length) {
        point[systemShort(s)] = sysData.T50_K[idx];
      }
    });
    return point;
  });

  return (
    <div>
      <div className={PANEL_LABEL}>(d) T₅₀ vs Pressure</div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <ReferenceArea y1={233.15} y2={358.15} fill="#10b981" fillOpacity={0.12} />
          <XAxis dataKey="pressure" tick={{ fontSize: 11 }} scale="log" domain={['auto', 'auto']}
            type="number" label={{ value: 'Pressure (bar)', position: 'insideBottom', offset: -2, fontSize: 11 }}
            tickFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) : '—')} />
          <YAxis tick={{ fontSize: 11 }} domain={[220, 385]} width={60}
            label={{ value: 'T₅₀ (K)', angle: -90, position: 'insideLeft', fontSize: 11, dx: -8 }}
            tickFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(0) : '—')} />
          <Tooltip formatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(1) + ' K' : '—')} labelFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) + ' bar' : '—')} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          {systems.map(s => (
            <Line key={s} type="monotone" dataKey={systemShort(s)} stroke={systemColor(s)}
              strokeWidth={1.5} dot={{ r: 3 }} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Panel (e): Coverage vs Temperature ───
function PanelCoverageVsTemp({ covTData }) {
  if (!covTData || Object.keys(covTData).length === 0) return null;

  const systems = Object.keys(covTData);
  const order = ['Pristine', '1Zr', '2Zr'];
  systems.sort((a, b) => order.indexOf(systemShort(a)) - order.indexOf(systemShort(b)));

  // Downsample to ~50 points for performance
  const refSys = systems[0];
  const sysData = covTData[refSys];
  if (!sysData || !Array.isArray(sysData.temperatures_K) || sysData.temperatures_K.length === 0) return null;

  const temps = sysData.temperatures_K;
  const step = Math.max(1, Math.floor(temps.length / 50));
  const chartData = [];
  for (let i = 0; i < temps.length; i += step) {
    const point = { T: temps[i] };
    systems.forEach(s => {
      const data = covTData[s];
      if (data && Array.isArray(data.coverages) && i < data.coverages.length) {
        point[systemShort(s)] = data.coverages[i];
      }
    });
    chartData.push(point);
  }

  return (
    <div>
      <div className={PANEL_LABEL}>(e) Coverage vs Temperature (1 bar)</div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 35, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <ReferenceArea x1={233} x2={358} fill="#10b981" fillOpacity={0.12} />
          <XAxis dataKey="T" tick={{ fontSize: 11 }} type="number" domain={['auto', 'auto']}
            label={{ value: 'Temperature (K)', position: 'insideBottom', offset: -2, fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} width={45}
            tickFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(1) : '—')}
            label={{ value: 'Coverage θ', angle: -90, position: 'insideLeft', fontSize: 11, dx: -5 }} />
          <Tooltip formatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) : '—')} labelFormatter={v => (typeof v === 'number' && !isNaN(v) ? v + ' K' : '—')} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          {systems.map(s => (
            <Line key={s} type="monotone" dataKey={systemShort(s)} stroke={systemColor(s)}
              strokeWidth={1.5} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Panel (f): Coverage vs Pressure ───
function PanelCoverageVsPressure({ covPData }) {
  if (!covPData || Object.keys(covPData).length === 0) return null;

  const systems = Object.keys(covPData);
  const order = ['Pristine', '1Zr', '2Zr'];
  systems.sort((a, b) => order.indexOf(systemShort(a)) - order.indexOf(systemShort(b)));

  const refSys = systems[0];
  const sysData = covPData[refSys];
  if (!sysData || !Array.isArray(sysData.pressures_bar) || sysData.pressures_bar.length === 0) return null;

  const pressures = sysData.pressures_bar;
  const step = Math.max(1, Math.floor(pressures.length / 50));
  const chartData = [];
  for (let i = 0; i < pressures.length; i += step) {
    const point = { P: pressures[i] };
    systems.forEach(s => {
      const data = covPData[s];
      if (data && Array.isArray(data.coverages) && i < data.coverages.length) {
        point[systemShort(s)] = data.coverages[i];
      }
    });
    chartData.push(point);
  }

  return (
    <div>
      <div className={PANEL_LABEL}>(f) Coverage vs Pressure (298 K)</div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 35, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="P" tick={{ fontSize: 11 }} scale="log" domain={['auto', 'auto']}
            type="number" label={{ value: 'Pressure (bar)', position: 'insideBottom', offset: -2, fontSize: 11 }}
            tickFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) : '—')} />
          <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} width={45}
            tickFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(1) : '—')}
            label={{ value: 'Coverage θ', angle: -90, position: 'insideLeft', fontSize: 11, dx: -5 }} />
          <Tooltip formatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) : '—')} labelFormatter={v => (typeof v === 'number' && !isNaN(v) ? v.toFixed(3) + ' bar' : '—')} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          {systems.map(s => (
            <Line key={s} type="monotone" dataKey={systemShort(s)} stroke={systemColor(s)}
              strokeWidth={1.5} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Main Mega-Panel Component ───
export default function PublicationFigures({ project }) {
  const [eads, setEads] = useState(null);
  const [decomp, setDecomp] = useState(null);
  const [shifts, setShifts] = useState(null);
  const [t50, setT50] = useState(null);
  const [covP, setCovP] = useState(null);
  const [covT, setCovT] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getAdsorptionEnergies(project).catch(() => null),
      getEnergyDecomposition(project).catch(() => null),
      getShifts(project).catch(() => null),
      getT50(project).catch(() => null),
      getCoverageP(project).catch(() => null),
      getCoverageT(project).catch(() => null),
    ]).then(([e, d, s, t, cp, ct]) => {
      setEads(e);
      setDecomp(d);
      setShifts(s);
      setT50(t);
      setCovP(cp);
      setCovT(ct);
      setLoading(false);
    });
  }, [project]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600 mr-2" />
        <span className="text-slate-500 text-sm">Loading publication figures...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Publication Figures</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border border-slate-100 rounded-lg p-3">
          <PanelEadsLollipop eadsData={eads} />
        </div>
        {decomp?.found && (
          <div className="border border-slate-100 rounded-lg p-3">
            <PanelEnergyDecomposition decompData={decomp} />
          </div>
        )}
        <div className="border border-slate-100 rounded-lg p-3">
          <PanelDescriptorShifts shiftsData={shifts} />
        </div>
        <div className="border border-slate-100 rounded-lg p-3">
          <PanelT50vsPressure t50Data={t50} />
        </div>
        <div className="border border-slate-100 rounded-lg p-3">
          <PanelCoverageVsTemp covTData={covT} />
        </div>
        <div className="border border-slate-100 rounded-lg p-3">
          <PanelCoverageVsPressure covPData={covP} />
        </div>
      </div>
    </div>
  );
}
