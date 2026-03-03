import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Wifi, WifiOff, Loader2 } from 'lucide-react';
import { useGraphStore } from '../store/graph';
import { fetchStatus } from '../api/client';
import type { HealthStatus, HeuristicMeta } from '../types/graph';

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function SettingsModal({ open, onClose }: Props) {
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<HealthStatus | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  const setBackendOnline = useGraphStore((s) => s.setBackendOnline);
  const hiddenHeuristics = useGraphStore((s) => s.hiddenHeuristics);
  const setHiddenHeuristics = useGraphStore((s) => s.setHiddenHeuristics);

  // Fetch real status whenever the modal opens
  useEffect(() => {
    if (!open) return;
    setTestError(null);
    fetchStatus()
      .then((s) => { setStatus(s); setBackendOnline(s.node_online); })
      .catch(() => { setStatus(null); setBackendOnline(false); });
  }, [open, setBackendOnline]);

  async function testConnection() {
    setTesting(true);
    setTestError(null);
    try {
      const s = await fetchStatus();
      setStatus(s);
      setBackendOnline(s.node_online);
    } catch (e: unknown) {
      setTestError(e instanceof Error ? e.message : 'Connection failed');
      setBackendOnline(false);
    } finally {
      setTesting(false);
    }
  }

  function toggleHeuristic(key: string) {
    const next = new Set(hiddenHeuristics);
    next.has(key) ? next.delete(key) : next.add(key);
    setHiddenHeuristics(next);
  }

  const heuristics: HeuristicMeta[] = status?.heuristics ?? [];

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            key="backdrop"
            className="fixed inset-0 bg-black/25 dark:bg-black/50 z-30"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            key="modal"
            className="fixed inset-0 flex items-center justify-center z-40 pointer-events-none"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 30, stiffness: 350 }}
          >
            <div className="pointer-events-auto w-full max-w-md mx-4 bg-[var(--bg)] border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
                <h2 className="font-bold text-[var(--fg)]">Settings</h2>
                <button onClick={onClose} className="text-[var(--fg-muted)] hover:text-[var(--fg)] transition">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="max-h-[70vh] overflow-y-auto">
                {/* Node status */}
                <div className="px-5 py-4 border-b border-[var(--border)]">
                  <h3 className="font-semibold text-sm text-[var(--fg)] mb-3">Node Status</h3>

                  {status ? (
                    <div className="grid grid-cols-2 gap-x-4 gap-y-2 mb-3">
                      <StatusRow label="Type" value={status.node_type} />
                      <StatusRow label="Network" value={status.network} />
                      <StatusRow label="Host" value={`${status.node_host}:${status.node_port}`} mono />
                      <StatusRow
                        label="Block height"
                        value={status.block_height !== null ? status.block_height.toLocaleString() : '—'}
                        mono
                      />
                      <div className="col-span-2 flex items-center gap-2 mt-1">
                        <span
                          className={`w-2 h-2 rounded-full ${status.node_online ? 'bg-green-500' : 'bg-red-400'}`}
                        />
                        <span className={`text-xs font-semibold ${status.node_online ? 'text-green-600 dark:text-green-400' : 'text-red-500'}`}>
                          {status.node_online ? 'Node reachable' : 'Node unreachable'}
                        </span>
                        <span className="text-xs text-[var(--fg-muted)]">· v{status.version}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-[var(--fg-muted)] mb-3 italic">
                      Backend not responding — is the server running on port 5050?
                    </p>
                  )}

                  <div className="flex items-center gap-3">
                    <button
                      onClick={testConnection}
                      disabled={testing}
                      className="px-4 h-8 rounded-lg bg-[var(--bg-subtle)] border border-[var(--border)] text-sm font-medium text-[var(--fg)] hover:border-[var(--color-btc)] hover:text-[var(--color-btc)] transition disabled:opacity-50 flex items-center gap-1.5"
                    >
                      {testing
                        ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Checking…</>
                        : <><Wifi className="w-3.5 h-3.5" /> Re-check</>}
                    </button>
                    {testError && (
                      <span className="flex items-center gap-1.5 text-xs text-red-500 font-semibold animate-fade-up">
                        <WifiOff className="w-3.5 h-3.5" /> {testError}
                      </span>
                    )}
                  </div>

                  <p className="mt-2 text-[10px] text-[var(--fg-muted)] leading-relaxed">
                    Configure your node in{' '}
                    <span className="font-mono bg-[var(--bg-subtle)] px-1 py-0.5 rounded">kycc.toml</span>,
                    then restart the backend. See{' '}
                    <span className="font-mono">docs/REGTEST_SETUP.md</span> for local setup.
                  </p>
                </div>

                {/* Fingerprint heuristics */}
                <div className="px-5 py-4">
                  <h3 className="font-semibold text-sm text-[var(--fg)] mb-1">Fingerprint Heuristics</h3>
                  <p className="text-[10px] text-[var(--fg-muted)] mb-3">
                    Toggle which heuristic annotations are shown on transaction nodes.
                    Enabled heuristics come from <span className="font-mono">kycc.toml</span>.
                  </p>

                  {heuristics.length === 0 ? (
                    <p className="text-xs text-[var(--fg-muted)] italic">
                      Connect to backend to load heuristic list.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {heuristics.map((h) => {
                        const isHidden = hiddenHeuristics.has(h.key);
                        const isDisabledByConfig = !h.enabled;
                        return (
                          <label key={h.key} className="flex items-start gap-3 cursor-pointer group">
                            <div
                              onClick={() => !isDisabledByConfig && toggleHeuristic(h.key)}
                              className={`mt-0.5 w-9 h-5 rounded-full transition-colors shrink-0 relative
                                ${isDisabledByConfig ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
                                ${!isHidden && !isDisabledByConfig ? 'bg-[var(--color-btc)]' : 'bg-[var(--border)]'}`}
                            >
                              <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${!isHidden && !isDisabledByConfig ? 'translate-x-4' : 'translate-x-0.5'}`} />
                            </div>
                            <div>
                              <div className="flex items-center gap-1.5">
                                <p className="font-mono text-xs font-semibold text-[var(--fg)] group-hover:text-[var(--color-btc)] transition-colors">
                                  {h.display}
                                </p>
                                {isDisabledByConfig && (
                                  <span className="text-[9px] px-1 rounded bg-[var(--bg-subtle)] border border-[var(--border)] text-[var(--fg-muted)]">
                                    off in config
                                  </span>
                                )}
                              </div>
                              <p className="text-[10px] text-[var(--fg-muted)]">{h.desc}</p>
                              <p className="text-[9px] font-mono text-[var(--fg-muted)] opacity-60 mt-0.5">
                                {h.codes.join(', ')}
                              </p>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              <div className="px-5 py-3 border-t border-[var(--border)] flex justify-end">
                <button
                  onClick={onClose}
                  className="px-5 h-8 rounded-lg bg-[var(--color-btc)] text-white text-sm font-semibold hover:opacity-90 transition"
                >
                  Done
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function StatusRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <p className="text-[10px] text-[var(--fg-muted)]">{label}</p>
      <p className={`text-xs font-semibold text-[var(--fg)] ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  );
}
