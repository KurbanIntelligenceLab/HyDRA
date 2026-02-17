const BASE = '/api';

// Session management
function getSessionId() {
  return localStorage.getItem('hydra_session_id');
}

function setSessionId(sessionId) {
  localStorage.setItem('hydra_session_id', sessionId);
}

async function fetchJson(url, options = {}) {
  // Add session ID to headers if available
  const sessionId = getSessionId();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  const res = await fetch(`${BASE}${url}`, {
    headers,
    credentials: 'include', // Include cookies for session management
    ...options,
  });

  // Extract and save session ID from response header
  const responseSessionId = res.headers.get('X-Session-ID');
  if (responseSessionId) {
    setSessionId(responseSessionId);
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// Projects
export const getProjects = () => fetchJson('/projects');
export const createProject = (name) => fetchJson('/projects', { method: 'POST', body: JSON.stringify({ name }) });

export async function uploadCsv(project, file) {
  const form = new FormData();
  form.append('file', file);

  const sessionId = getSessionId();
  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  const res = await fetch(`${BASE}/projects/${project}/upload-csv`, {
    method: 'POST',
    body: form,
    headers,
    credentials: 'include',
  });

  // Extract and save session ID from response
  const responseSessionId = res.headers.get('X-Session-ID');
  if (responseSessionId) {
    setSessionId(responseSessionId);
  }

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadXyz(project, file) {
  const form = new FormData();
  form.append('file', file);

  const sessionId = getSessionId();
  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  const res = await fetch(`${BASE}/projects/${project}/upload-xyz`, {
    method: 'POST',
    body: form,
    headers,
    credentials: 'include',
  });

  // Extract and save session ID from response
  const responseSessionId = res.headers.get('X-Session-ID');
  if (responseSessionId) {
    setSessionId(responseSessionId);
  }

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Chat
export const sendChat = (query, project) =>
  fetchJson('/chat', { method: 'POST', body: JSON.stringify({ query, project }) });

// Data
export const getDescriptors = (project) => fetchJson(`/data/${project}/descriptors`);
export const getCorrelation = (project) => fetchJson(`/data/${project}/correlation`);
export const getShifts = (project) => fetchJson(`/data/${project}/shifts`);
export const getStructures = (project) => fetchJson(`/data/${project}/structures`);
export const getStructure = (project, label) => fetchJson(`/data/${project}/structure/${label}`);
export const getCharges = (project, label) => fetchJson(`/data/${project}/charges/${label}`);
export const getAdsorptionEnergies = (project) => fetchJson(`/data/${project}/adsorption-energies`);
export const getEnergyDecomposition = (project) => fetchJson(`/data/${project}/energy-decomposition`);

// Thermo
export const getCoverageP = (project, opts = {}) =>
  fetchJson(`/thermo/${project}/coverage-vs-pressure`, { method: 'POST', body: JSON.stringify(opts) });
export const getCoverageT = (project, opts = {}) =>
  fetchJson(`/thermo/${project}/coverage-vs-temperature`, { method: 'POST', body: JSON.stringify(opts) });
export const getT50 = (project, opts = {}) =>
  fetchJson(`/thermo/${project}/t50`, { method: 'POST', body: JSON.stringify(opts) });
export const compareSystems = (project, opts = {}) =>
  fetchJson(`/thermo/${project}/compare`, { method: 'POST', body: JSON.stringify(opts) });

// ML
export const runSymbolicRegression = (project) =>
  fetchJson(`/ml/${project}/symbolic-regression`, { method: 'POST' });
export const runGP = (project) =>
  fetchJson(`/ml/${project}/gp-predict`, { method: 'POST' });
export const suggestNext = (project) =>
  fetchJson(`/ml/${project}/suggest-next`, { method: 'POST' });
export const featureImportance = (project) =>
  fetchJson(`/ml/${project}/feature-importance`, { method: 'POST' });
