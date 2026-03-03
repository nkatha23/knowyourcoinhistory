import { useEffect, useState } from 'react';
import { Toaster } from 'sonner';
import './App.css';
import Toolbar from './components/Toolbar';
import GraphCanvas from './components/Graph/GraphCanvas';
import RightPanel from './components/RightPanel';
import SettingsModal from './components/SettingsModal';
import { useGraphStore } from './store/graph';
import { fetchHealth, fetchSessions } from './api/client';

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const setBackendOnline = useGraphStore((s) => s.setBackendOnline);
  const setRecentSessions = useGraphStore((s) => s.setRecentSessions);
  const theme = useGraphStore((s) => s.theme);

  // Probe backend on mount and load recent sessions
  useEffect(() => {
    fetchHealth()
      .then(() => {
        setBackendOnline(true);
        return fetchSessions();
      })
      .then((r) => setRecentSessions(r.sessions))
      .catch(() => setBackendOnline(false));
  }, [setBackendOnline, setRecentSessions]);

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <Toolbar onOpenSettings={() => setSettingsOpen(true)} />

      <div className="relative flex-1 overflow-hidden">
        <GraphCanvas />
        <RightPanel />
      </div>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      <Toaster
        position="bottom-left"
        theme={theme}
        toastOptions={{
          style: {
            fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
            fontSize: '13px',
          },
        }}
      />
    </div>
  );
}
