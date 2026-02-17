import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Global debug helper
window.dumpDescriptorLogs = () => {
  const logs = JSON.parse(localStorage.getItem('descriptorDebugLogs') || '[]');
  console.table(logs);
  console.log('Full logs:', logs);
  return logs;
};

console.log('%c💡 Tip: Run window.dumpDescriptorLogs() to see all descriptor debug logs', 'background: #222; color: #4ec9b0; font-size: 14px; padding: 5px;');

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
