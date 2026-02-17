import { useState, useEffect } from 'react';
import { Atom, MessageSquare, Database, Brain, Eye, Upload } from 'lucide-react';
import { getProjects } from './api';
import ChatPanel from './components/ChatPanel';
import DescriptorDashboard from './components/DescriptorDashboard';
import MoleculeViewer from './components/MoleculeViewer';
import MLInsights from './components/MLInsights';
import AgentWorkflow from './components/AgentWorkflow';
import DataUpload from './components/DataUpload';
import ProjectSelector from './components/ProjectSelector';

const TABS = [
  { id: 'chat', label: 'Agent Chat', icon: MessageSquare },
  { id: 'structure', label: '3D Structures', icon: Atom },
  { id: 'descriptors', label: 'Descriptors', icon: Database },
  { id: 'ml', label: 'ML Insights', icon: Brain },
  { id: 'workflow', label: 'Agent Workflow', icon: Eye },
  { id: 'upload', label: 'Upload Data', icon: Upload },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [project, setProject] = useState('zr-tio2');
  const [projects, setProjects] = useState([]);
  const [agentLog, setAgentLog] = useState([]);

  useEffect(() => {
    getProjects().then(setProjects).catch(() => {});
  }, []);

  const refreshProjects = () => getProjects().then(setProjects).catch(() => {});

  const addAgentLog = (entry) => {
    setAgentLog((prev) => [...prev, { ...entry, timestamp: new Date().toISOString() }]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Atom className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">HyDRA</h1>
              <p className="text-xs text-slate-500">Hydrogen Discovery via Reactive Agents</p>
            </div>
          </div>
          <ProjectSelector
            project={project}
            setProject={setProject}
            projects={projects}
            onRefresh={refreshProjects}
          />
        </div>
      </header>

      {/* Tab bar */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-[1400px] mx-auto px-6 flex gap-1 overflow-x-auto">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-[1400px] mx-auto p-6">
        {activeTab === 'chat' && (
          <ChatPanel project={project} onAgentActivity={addAgentLog} />
        )}
        {activeTab === 'structure' && (
          <MoleculeViewer project={project} />
        )}
        {activeTab === 'descriptors' && (
          <DescriptorDashboard project={project} />
        )}
        {activeTab === 'ml' && (
          <MLInsights project={project} />
        )}
        {activeTab === 'workflow' && (
          <AgentWorkflow log={agentLog} />
        )}
        {activeTab === 'upload' && (
          <DataUpload
            projects={projects}
            onProjectCreated={refreshProjects}
          />
        )}
      </main>
    </div>
  );
}
