import { Eye, Bot, Clock, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

const AGENT_STYLES = {
  descriptor: { color: 'bg-purple-100 text-purple-700 border-purple-200', label: 'Descriptor Analyst' },
  structure: { color: 'bg-green-100 text-green-700 border-green-200', label: 'Structure Analyst' },
  thermo: { color: 'bg-orange-100 text-orange-700 border-orange-200', label: 'Thermodynamics' },
  screening: { color: 'bg-blue-100 text-blue-700 border-blue-200', label: 'ML Screening' },
  reasoning: { color: 'bg-rose-100 text-rose-700 border-rose-200', label: 'Reasoning' },
};

export default function AgentWorkflow({ log }) {
  const [expandedIdx, setExpandedIdx] = useState(null);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
          <Eye className="w-5 h-5 text-blue-600" />
          Agent Workflow Log
        </h2>
        <p className="text-sm text-slate-500 mb-4">
          See which agents were invoked for each query and what they computed.
        </p>

        {log.length === 0 ? (
          <div className="text-center py-16 text-slate-400">
            <Bot className="w-12 h-12 mx-auto mb-3" />
            <p className="text-sm">No agent activity yet. Ask a question in the chat to see the workflow.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {log.map((entry, idx) => (
              <div key={idx} className="border border-slate-200 rounded-lg overflow-hidden">
                {/* Header */}
                <button
                  onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
                  className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span className="text-xs text-slate-400">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-sm text-slate-700 font-medium truncate max-w-md">
                      {entry.query}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {entry.agents?.map((a) => (
                      <span
                        key={a}
                        className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${
                          AGENT_STYLES[a]?.color || 'bg-slate-100 text-slate-600 border-slate-200'
                        }`}
                      >
                        {AGENT_STYLES[a]?.label || a}
                      </span>
                    ))}
                    {expandedIdx === idx ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </button>

                {/* Expanded details */}
                {expandedIdx === idx && entry.agentResults && (
                  <div className="border-t border-slate-100 p-4 bg-slate-50">
                    <div className="space-y-4">
                      {Object.entries(entry.agentResults).map(([agentName, result]) => (
                        <div key={agentName}>
                          <div className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium border mb-2 ${
                            AGENT_STYLES[agentName]?.color || 'bg-slate-100 text-slate-600 border-slate-200'
                          }`}>
                            {AGENT_STYLES[agentName]?.label || agentName}
                          </div>
                          <pre className="text-[11px] bg-white rounded-lg p-3 overflow-x-auto border border-slate-200 max-h-60 overflow-y-auto">
                            {typeof result === 'string'
                              ? result
                              : JSON.stringify(result, null, 2).slice(0, 2000)
                            }
                            {JSON.stringify(result).length > 2000 && '\n... (truncated)'}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Agent legend */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Agent Architecture</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {Object.entries(AGENT_STYLES).map(([key, style]) => (
            <div key={key} className={`rounded-lg p-3 border ${style.color}`}>
              <div className="font-medium text-sm">{style.label}</div>
              <div className="text-[10px] mt-1 opacity-75">
                {key === 'descriptor' && 'HOMO, LUMO, correlations, CDFT indices'}
                {key === 'structure' && 'XYZ parsing, coordination, charges, 3D viz'}
                {key === 'thermo' && 'Langmuir, T_50, coverage, DOE feasibility'}
                {key === 'screening' && 'PySR, GP, active learning, feature importance'}
                {key === 'reasoning' && 'Mechanistic interpretation, literature context'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
