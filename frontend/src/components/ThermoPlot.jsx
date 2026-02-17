import { useState, useEffect } from 'react';
import { FlaskConical, Loader2 } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ReferenceLine, ReferenceArea,
} from 'recharts';
import { getT50, getCoverageP, getCoverageT, compareSystems } from '../api';
import { MathNotation } from '../utils/mathNotation';

const SYSTEM_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899'];

export default function ThermoPlot({ project }) {
  const [t50Data, setT50Data] = useState(null);
  const [coverageP, setCoverageP] = useState(null);
  const [coverageT, setCoverageT] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getT50(project).catch(() => null),
      getCoverageP(project).catch(() => null),
      getCoverageT(project).catch(() => null),
      compareSystems(project).catch(() => null),
    ]).then(([t50, cvgP, cvgT, comp]) => {
      setT50Data(t50);
      setCoverageP(cvgP);
      setCoverageT(cvgT);
      setComparison(comp);
      setLoading(false);
    });
  }, [project]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-2" />
        <span className="text-slate-500">Computing thermodynamics...</span>
      </div>
    );
  }

  // Build T50 chart data
  const t50ChartData = [];
  if (t50Data) {
    const systems = Object.keys(t50Data);
    const firstSystem = t50Data[systems[0]];
    if (firstSystem?.pressures_bar) {
      for (let i = 0; i < firstSystem.pressures_bar.length; i++) {
        const point = { P_bar: firstSystem.pressures_bar[i] };
        for (const sys of systems) {
          point[sys] = t50Data[sys].t50_K[i] - 273.15; // Convert to °C
        }
        t50ChartData.push(point);
      }
    }
  }

  // Build coverage vs pressure chart data
  const cvgPChartData = [];
  if (coverageP) {
    const systems = Object.keys(coverageP);
    const firstSystem = coverageP[systems[0]];
    if (firstSystem?.pressures_bar) {
      for (let i = 0; i < firstSystem.pressures_bar.length; i++) {
        const point = { P_bar: firstSystem.pressures_bar[i] };
        for (const sys of systems) {
          point[sys] = coverageP[sys].coverages[i];
        }
        cvgPChartData.push(point);
      }
    }
  }

  // Build coverage vs temperature chart data
  const cvgTChartData = [];
  if (coverageT) {
    const systems = Object.keys(coverageT);
    const firstSystem = coverageT[systems[0]];
    if (firstSystem?.temperatures_K) {
      for (let i = 0; i < firstSystem.temperatures_K.length; i++) {
        const point = { T_C: firstSystem.temperatures_K[i] - 273.15 };
        for (const sys of systems) {
          point[sys] = coverageT[sys].coverages[i];
        }
        cvgTChartData.push(point);
      }
    }
  }

  const systemNames = t50Data ? Object.keys(t50Data) : [];

  return (
    <div className="space-y-6">
      {/* Comparison summary */}
      {comparison?.systems && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-orange-500" />
            System Comparison at {comparison.P_bar} bar
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {comparison.systems.map((sys, i) => (
              <div key={sys.system} className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                <div className="text-sm font-bold text-slate-800 mb-2">{sys.system}</div>
                <div className="space-y-1 text-xs text-slate-600">
                  <div><MathNotation.Eads />: <span className="font-mono font-bold">{sys.E_ads_eV.toFixed(2)} eV</span> ({sys.E_ads_kJmol.toFixed(2)} kJ/mol)</div>
                  <div><MathNotation.T50 />: <span className="font-mono font-bold">{sys.T50_C.toFixed(0)}°C</span> ({sys.T50_K.toFixed(0)} K)</div>
                  <div>Coverage at 298K: <span className="font-mono font-bold">{(sys.theta_298K * 100).toFixed(1)}%</span></div>
                  <div className={`mt-1 px-2 py-0.5 rounded text-[10px] inline-block ${
                    sys.in_doe_window ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {sys.in_doe_window ? 'In DOE window' : 'Outside DOE window'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* T50 vs Pressure */}
      {t50ChartData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">
            Desorption Midpoint Temperature (<MathNotation.T50 />) vs Pressure
          </h2>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={t50ChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="P_bar" label={{ value: 'Pressure (bar)', position: 'insideBottom', offset: -5 }} tick={{ fontSize: 11 }} scale="log" domain={['auto', 'auto']} tickFormatter={(v) => v.toFixed(2)} />
              <YAxis label={{ value: 'T₅₀ (°C)', angle: -90, position: 'insideLeft' }} tick={{ fontSize: 11 }} tickFormatter={(v) => v.toFixed(2)} />
              <Tooltip formatter={(v) => `${v.toFixed(2)}°C`} />
              <Legend />
              <ReferenceArea y1={-40} y2={85} fill="#10b981" fillOpacity={0.1} label={{ value: 'DOE Window', fill: '#10b981', fontSize: 10 }} />
              <ReferenceLine y={-40} stroke="#10b981" strokeDasharray="5 5" />
              <ReferenceLine y={85} stroke="#10b981" strokeDasharray="5 5" />
              {systemNames.map((sys, i) => (
                <Line key={sys} type="monotone" dataKey={sys} stroke={SYSTEM_COLORS[i % SYSTEM_COLORS.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Coverage vs Pressure */}
      {cvgPChartData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Coverage vs Pressure (298 K)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={cvgPChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="P_bar" label={{ value: 'Pressure (bar)', position: 'insideBottom', offset: -5 }} tick={{ fontSize: 11 }} scale="log" domain={['auto', 'auto']} tickFormatter={(v) => v.toFixed(2)} />
              <YAxis label={{ value: 'Coverage (θ)', angle: -90, position: 'insideLeft' }} tick={{ fontSize: 11 }} domain={[0, 1]} tickFormatter={(v) => v.toFixed(2)} />
              <Tooltip formatter={(v) => v.toFixed(2)} />
              <Legend />
              {systemNames.map((sys, i) => (
                <Line key={sys} type="monotone" dataKey={sys} stroke={SYSTEM_COLORS[i % SYSTEM_COLORS.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Coverage vs Temperature */}
      {cvgTChartData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Coverage vs Temperature (1 bar)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={cvgTChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="T_C" label={{ value: 'Temperature (°C)', position: 'insideBottom', offset: -5 }} tick={{ fontSize: 11 }} tickFormatter={(v) => v.toFixed(2)} />
              <YAxis label={{ value: 'Coverage (θ)', angle: -90, position: 'insideLeft' }} tick={{ fontSize: 11 }} domain={[0, 1]} tickFormatter={(v) => v.toFixed(2)} />
              <Tooltip formatter={(v) => v.toFixed(2)} />
              <Legend />
              <ReferenceArea x1={-40} x2={85} fill="#10b981" fillOpacity={0.1} />
              {systemNames.map((sys, i) => (
                <Line key={sys} type="monotone" dataKey={sys} stroke={SYSTEM_COLORS[i % SYSTEM_COLORS.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
