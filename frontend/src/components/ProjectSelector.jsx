import { FolderOpen, RefreshCw } from 'lucide-react';

export default function ProjectSelector({ project, setProject, projects, onRefresh }) {
  return (
    <div className="flex items-center gap-2">
      <FolderOpen className="w-4 h-4 text-slate-400" />
      <select
        value={project}
        onChange={(e) => setProject(e.target.value)}
        className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {projects.map((p) => (
          <option key={p.name} value={p.name}>
            {p.name} {p.builtin ? '(built-in)' : ''} — {p.systems?.length || 0} systems
          </option>
        ))}
        {projects.length === 0 && <option value="zr-tio2">zr-tio2</option>}
      </select>
      <button
        onClick={onRefresh}
        className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"
        title="Refresh projects"
      >
        <RefreshCw className="w-4 h-4" />
      </button>
    </div>
  );
}
