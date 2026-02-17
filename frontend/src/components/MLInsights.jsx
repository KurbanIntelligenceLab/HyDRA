import { useState, useEffect } from 'react';
import { Brain, Loader2, Play, Sparkles, TrendingUp, Target } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter, ErrorBar, Cell, Legend,
} from 'recharts';
import { runSymbolicRegression, runGP, suggestNext, featureImportance } from '../api';
import { MathNotation } from '../utils/mathNotation';

const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#a855f7'];

export default function MLInsights({ project }) {
  const [symReg, setSymReg] = useState(null);
  const [gp, setGp] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [importance, setImportance] = useState(null);
  const [loading, setLoading] = useState({});

  const runAnalysis = async (key, fn, setter) => {
    setLoading((prev) => ({ ...prev, [key]: true }));
    try {
      const result = await fn(project);
      setter(result);
    } catch (err) {
      setter({ error: err.message });
    }
    setLoading((prev) => ({ ...prev, [key]: false }));
  };

  // GP predictions chart data
  const gpChartData = [];
  if (gp?.predictions && gp?.candidate_labels) {
    for (let i = 0; i < gp.candidate_labels.length; i++) {
      gpChartData.push({
        element: gp.candidate_labels[i],
        predicted: gp.predictions[i],
        uncertainty: gp.uncertainties[i],
        errorY: [gp.uncertainties[i], gp.uncertainties[i]],
      });
    }
    gpChartData.sort((a, b) => a.predicted - b.predicted);
  }

  // Feature importance chart data
  const importanceChartData = importance?.ranked_features?.map((f) => ({
    feature: f.feature,
    correlation: Math.abs(f.correlation_with_target),
    sign: f.correlation_with_target > 0 ? 'positive' : 'negative',
  })) || [];

  return (
    <div className="space-y-6">
      {/* Control panel */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Brain className="w-5 h-5 text-blue-600" />
          Interpretable ML Analysis
        </h2>
        <p className="text-sm text-slate-500 mb-4">
          Run ML analyses on your materials data. These methods are designed for small datasets
          and provide interpretable, physically meaningful results.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => runAnalysis('symReg', runSymbolicRegression, setSymReg)}
            disabled={loading.symReg}
            className="flex items-center gap-2 bg-purple-50 hover:bg-purple-100 border border-purple-200 text-purple-700 px-4 py-3 rounded-xl transition-colors text-sm font-medium disabled:opacity-50"
          >
            {loading.symReg ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Symbolic Regression
          </button>
          <button
            onClick={() => runAnalysis('gp', runGP, setGp)}
            disabled={loading.gp}
            className="flex items-center gap-2 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 px-4 py-3 rounded-xl transition-colors text-sm font-medium disabled:opacity-50"
          >
            {loading.gp ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
            GP Predictions
          </button>
          <button
            onClick={() => runAnalysis('suggest', suggestNext, setSuggestions)}
            disabled={loading.suggest}
            className="flex items-center gap-2 bg-green-50 hover:bg-green-100 border border-green-200 text-green-700 px-4 py-3 rounded-xl transition-colors text-sm font-medium disabled:opacity-50"
          >
            {loading.suggest ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
            Suggest Next
          </button>
          <button
            onClick={() => runAnalysis('importance', featureImportance, setImportance)}
            disabled={loading.importance}
            className="flex items-center gap-2 bg-orange-50 hover:bg-orange-100 border border-orange-200 text-orange-700 px-4 py-3 rounded-xl transition-colors text-sm font-medium disabled:opacity-50"
          >
            {loading.importance ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Feature Importance
          </button>
        </div>
      </div>

      {/* Symbolic Regression Results */}
      {symReg && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            Discovered Equations
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            {symReg.method} — {symReg.n_datapoints} data points
          </p>
          {symReg.error ? (
            <div className="text-red-600 text-sm">{symReg.error}</div>
          ) : (
            <>
              {symReg.best_equation && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                  <div className="text-xs text-purple-600 font-medium mb-1">Best Equation</div>
                  <code className="text-lg font-mono text-purple-800">{symReg.best_equation}</code>
                </div>
              )}
              {symReg.equations?.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium text-slate-600">All discovered equations (Pareto front):</div>
                  {symReg.equations.map((eq, i) => (
                    <div key={i} className="flex items-center gap-4 text-xs bg-slate-50 rounded-lg p-3">
                      <code className="flex-1 font-mono text-slate-800">{eq.equation}</code>
                      <span className="text-slate-500">complexity: {eq.complexity}</span>
                      <span className="text-slate-500">loss: {eq.loss?.toFixed(6)}</span>
                      {eq.r_squared !== undefined && (
                        <span className="text-blue-600 font-medium">R²: {eq.r_squared?.toFixed(4)}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {symReg.note && (
                <p className="text-xs text-slate-400 mt-3">{symReg.note}</p>
              )}
            </>
          )}
        </div>
      )}

      {/* GP Predictions */}
      {gp && !gp.error && gpChartData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Gaussian Process Predictions for Candidate Dopants
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Predicted <MathNotation.Eads /> with uncertainty. Larger error bars = more uncertain = more informative to test.
          </p>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={gpChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="element" tick={{ fontSize: 12 }} />
              <YAxis label={{ value: 'Predicted Eₐ𝒹ₛ (eV)', angle: -90, position: 'insideLeft' }} tick={{ fontSize: 11 }} tickFormatter={(v) => v.toFixed(2)} />
              <Tooltip formatter={(v) => `${v.toFixed(2)} eV`} />
              <Bar dataKey="predicted" name="Predicted Eads" radius={[4, 4, 0, 0]}>
                {gpChartData.map((entry, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {/* Uncertainty table */}
          <div className="mt-4 overflow-x-auto">
            <table className="text-xs w-full">
              <thead>
                <tr>
                  <th className="p-2 text-left text-slate-600">Element</th>
                  <th className="p-2 text-slate-600">Predicted <MathNotation.Eads /> (eV)</th>
                  <th className="p-2 text-slate-600">Uncertainty (eV)</th>
                </tr>
              </thead>
              <tbody>
                {gpChartData.map((row) => (
                  <tr key={row.element} className="border-t border-slate-100">
                    <td className="p-2 font-medium">{row.element}</td>
                    <td className="p-2 font-mono text-center">{row.predicted.toFixed(2)}</td>
                    <td className="p-2 font-mono text-center">{row.uncertainty.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Active Learning Suggestions */}
      {suggestions && !suggestions.error && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <Target className="w-5 h-5 text-green-600" />
            Next Experiment Suggestions
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            {suggestions.selection_criterion}
          </p>
          {suggestions.most_informative && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <div className="text-xs text-green-600 font-medium mb-1">Most Informative Next Experiment</div>
              <div className="text-xl font-bold text-green-800">{suggestions.most_informative}</div>
            </div>
          )}
          <div className="space-y-3">
            {suggestions.ranked_candidates?.map((cand, i) => (
              <div key={cand.element} className="flex items-start gap-4 bg-slate-50 rounded-lg p-4">
                <div className="bg-slate-200 text-slate-600 rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold flex-shrink-0">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-slate-800">{cand.element}</span>
                    <span className="text-xs text-slate-500">
                      <MathNotation.Eads />: {cand.predicted_E_ads_eV} eV | Uncertainty: {cand.uncertainty_eV} eV
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{cand.rationale}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature Importance */}
      {importance && !importance.error && importanceChartData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <Play className="w-5 h-5 text-orange-500" />
            Feature Importance
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Most important: <span className="font-bold">{importance.most_important}</span>
          </p>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={importanceChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" label={{ value: '|Correlation with Eₐ𝒹ₛ|', position: 'insideBottom', offset: -5 }} tick={{ fontSize: 11 }} domain={[0, 1]} />
              <YAxis type="category" dataKey="feature" tick={{ fontSize: 10 }} width={100} />
              <Tooltip />
              <Bar dataKey="correlation" name="|Correlation|" fill="#f59e0b" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
