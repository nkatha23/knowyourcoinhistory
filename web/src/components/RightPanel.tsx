import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Copy, Check, Tag, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';
import { useGraphStore } from '../store/graph';
import { saveLabel, deleteLabel } from '../api/client';
import type { AppNodeData, TxNodeData, UTXONodeData, Severity } from '../types/graph';

const SEV_STYLE: Record<Severity, { bar: string; badge: string; text: string }> = {
  info:    { bar: 'bg-blue-500',  badge: 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800', text: 'text-blue-700 dark:text-blue-300' },
  warning: { bar: 'bg-amber-500', badge: 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800', text: 'text-amber-700 dark:text-amber-300' },
  flag:    { bar: 'bg-red-500',   badge: 'bg-red-50 dark:bg-red-950/60 text-red-600 dark:text-red-300 border-red-200 dark:border-red-800', text: 'text-red-600 dark:text-red-300' },
};

const CATEGORIES = ['Self', 'Exchange', 'Counterparty', 'Miner', 'Unknown', 'Other'];

export default function RightPanel() {
  const selectedId = useGraphStore((s) => s.selectedId);
  const nodes = useGraphStore((s) => s.nodes);
  const selectNode = useGraphStore((s) => s.selectNode);
  const walletId = useGraphStore((s) => s.walletId);
  const refreshNodeLabel = useGraphStore((s) => s.refreshNodeLabel);

  const [labelText, setLabelText] = useState('');
  const [category, setCategory] = useState('Unknown');
  const [spendable, setSpendable] = useState(false);
  const [saved, setSaved] = useState(false);
  const [expandedAnnotations, setExpandedAnnotations] = useState<Set<number>>(new Set());
  const [copied, setCopied] = useState(false);

  const selectedNode = selectedId ? nodes.find((n) => n.id === selectedId) : null;
  const data = selectedNode?.data as AppNodeData | undefined;

  // Populate form when selection changes
  useEffect(() => {
    if (!data) return;
    setLabelText(data.label ?? '');
    setSaved(false);
    setExpandedAnnotations(new Set());
  }, [selectedId]);

  const isTx = data?.kind === 'tx';
  const txData = isTx ? (data as TxNodeData) : null;
  const utxoData = !isTx && data ? (data as UTXONodeData) : null;

  const identifier = txData?.txid ?? (utxoData ? `${utxoData.txid}:${utxoData.vout}` : '');
  const refType = isTx ? 'tx' : 'utxo';

  const handleSave = useCallback(async () => {
    if (!selectedId) return;
    try {
      await saveLabel({
        ref_type: refType,
        ref: identifier,
        label: labelText,
        wallet_id: walletId,
        spendable: !isTx ? spendable : undefined,
      });
      refreshNodeLabel(selectedId, labelText || null);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      toast.error('Failed to save label');
    }
  }, [selectedId, refType, identifier, labelText, walletId, spendable, isTx, refreshNodeLabel]);

  const handleDelete = useCallback(async () => {
    if (!selectedId) return;
    try {
      await deleteLabel({ ref_type: refType, ref: identifier, wallet_id: walletId });
      refreshNodeLabel(selectedId, null);
      setLabelText('');
      toast.success('Label removed');
    } catch {
      toast.error('Failed to delete label');
    }
  }, [selectedId, refType, identifier, walletId, refreshNodeLabel]);

  const copyId = () => {
    navigator.clipboard.writeText(identifier);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const annotations = txData?.annotations ?? [];

  return (
    <AnimatePresence>
      {selectedId && data && (
        <motion.aside
          key="panel"
          initial={{ x: 380 }}
          animate={{ x: 0 }}
          exit={{ x: 380 }}
          transition={{ type: 'spring', damping: 28, stiffness: 320 }}
          className="absolute right-0 top-0 h-full w-[380px] bg-[var(--bg)] border-l border-[var(--border)] shadow-xl flex flex-col z-10 overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-[var(--color-btc)] text-white">
                {isTx ? 'Transaction' : 'UTXO'}
              </span>
              {utxoData?.isInput && (
                <span className="text-xs text-[var(--fg-muted)]">Input</span>
              )}
              {utxoData && !utxoData.isInput && (
                <span className="text-xs text-[var(--fg-muted)]">Output</span>
              )}
            </div>
            <button
              onClick={() => selectNode(null)}
              className="text-[var(--fg-muted)] hover:text-[var(--fg)] transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {/* Identifier */}
            <div className="px-4 py-3 border-b border-[var(--border)]">
              <p className="text-[10px] uppercase tracking-wider text-[var(--fg-muted)] mb-1">
                {isTx ? 'Transaction ID' : 'UTXO Reference'}
              </p>
              <div className="flex items-center gap-2">
                <p className="font-mono text-xs text-[var(--fg)] break-all flex-1 leading-relaxed">
                  {identifier}
                </p>
                <button
                  onClick={copyId}
                  className="shrink-0 p-1.5 rounded-lg border border-[var(--border)] hover:bg-[var(--bg-subtle)] text-[var(--fg-muted)] hover:text-[var(--fg)] transition"
                  title="Copy"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* TX details */}
            {txData && (
              <div className="px-4 py-3 border-b border-[var(--border)] grid grid-cols-2 gap-x-4 gap-y-2">
                <Detail label="Block" value={txData.block_height?.toLocaleString() ?? 'Unconfirmed'} />
                <Detail label="Fee" value={txData.fee_sats !== null ? `${txData.fee_sats.toLocaleString()} sats` : '—'} mono />
                <Detail label="Inputs" value={String(txData.inputs.length)} />
                <Detail label="Outputs" value={String(txData.outputs.length)} />
                <Detail label="Size" value={txData.size ? `${txData.size} bytes` : '—'} />
                <Detail label="Version" value={String(txData.version)} />
                {txData.is_rbf && <Detail label="RBF" value="Yes" />}
                {txData.is_coinbase && <Detail label="Coinbase" value="Yes" />}
              </div>
            )}

            {/* UTXO details */}
            {utxoData && (
              <div className="px-4 py-3 border-b border-[var(--border)] grid grid-cols-2 gap-x-4 gap-y-2">
                <Detail label="Value" value={`${(utxoData.value_sats / 1e8).toFixed(8)} BTC`} mono />
                <Detail label="Sats" value={utxoData.value_sats.toLocaleString()} mono />
                <Detail label="Script" value={utxoData.script_type.toUpperCase()} />
                <Detail label="Status" value={utxoData.is_spent ? 'Spent' : 'Unspent'} />
                {utxoData.address && (
                  <div className="col-span-2">
                    <p className="text-[10px] text-[var(--fg-muted)] mb-0.5">Address</p>
                    <p className="font-mono text-xs text-[var(--fg)] break-all">{utxoData.address}</p>
                  </div>
                )}
              </div>
            )}

            {/* Label editor */}
            <div className="px-4 py-3 border-b border-[var(--border)]">
              <div className="flex items-center gap-1.5 mb-2">
                <Tag className="w-3.5 h-3.5 text-[var(--color-btc)]" />
                <p className="text-xs font-semibold text-[var(--fg)]">Label</p>
                {saved && (
                  <span className="animate-fade-up text-[10px] text-green-600 dark:text-green-400 font-semibold ml-1">
                    ✓ Saved
                  </span>
                )}
              </div>

              <input
                type="text"
                value={labelText}
                onChange={(e) => setLabelText(e.target.value)}
                onBlur={handleSave}
                placeholder="e.g. Exchange withdrawal, My cold wallet…"
                className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] text-[var(--fg)] placeholder:text-[var(--fg-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-btc)]/40 focus:border-[var(--color-btc)] transition"
              />

              <div className="flex items-center gap-2 mt-2">
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="flex-1 h-8 px-2 text-xs rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] text-[var(--fg)] focus:outline-none focus:ring-2 focus:ring-[var(--color-btc)]/40"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>

                {!isTx && (
                  <label className="flex items-center gap-1.5 text-xs text-[var(--fg-muted)] cursor-pointer shrink-0">
                    <div
                      onClick={() => setSpendable((s) => !s)}
                      className={`w-9 h-5 rounded-full transition-colors relative ${spendable ? 'bg-[var(--color-btc)]' : 'bg-[var(--border)]'}`}
                    >
                      <span
                        className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${spendable ? 'translate-x-4' : 'translate-x-0.5'}`}
                      />
                    </div>
                    Spendable
                  </label>
                )}
              </div>

              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleSave}
                  className="flex-1 h-8 rounded-lg bg-[var(--color-btc)] text-white text-xs font-semibold hover:opacity-90 transition"
                >
                  Save label
                </button>
                {labelText && (
                  <button
                    onClick={handleDelete}
                    className="h-8 px-3 rounded-lg border border-red-300 dark:border-red-800 text-red-600 dark:text-red-400 text-xs hover:bg-red-50 dark:hover:bg-red-950/30 transition"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>

            {/* Fingerprint annotations */}
            {annotations.length > 0 && (
              <div className="px-4 py-3">
                <p className="text-xs font-semibold text-[var(--fg)] mb-2">
                  🔍 Privacy Fingerprints ({annotations.length})
                </p>
                <div className="space-y-2">
                  {annotations.map((a, i) => {
                    const sty = SEV_STYLE[a.severity];
                    const expanded = expandedAnnotations.has(i);
                    return (
                      <div
                        key={i}
                        className={`rounded-lg border overflow-hidden ${sty.badge}`}
                      >
                        <button
                          className="w-full flex items-start gap-2 px-3 py-2 text-left"
                          onClick={() =>
                            setExpandedAnnotations((prev) => {
                              const next = new Set(prev);
                              expanded ? next.delete(i) : next.add(i);
                              return next;
                            })
                          }
                        >
                          <span className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${sty.bar}`} />
                          <div className="flex-1">
                            <p className="font-mono font-bold text-[11px]">{a.code}</p>
                            <p className="text-[10px] opacity-80 leading-snug mt-0.5">{a.description}</p>
                          </div>
                          {a.affected.length > 0 &&
                            (expanded ? <ChevronUp className="w-3.5 h-3.5 shrink-0 mt-0.5 opacity-60" /> : <ChevronDown className="w-3.5 h-3.5 shrink-0 mt-0.5 opacity-60" />)
                          }
                        </button>
                        {expanded && a.affected.length > 0 && (
                          <div className="px-3 pb-2 space-y-1">
                            {a.affected.map((addr, j) => (
                              <p key={j} className="font-mono text-[10px] break-all opacity-70">{addr}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Beginner tip */}
            <div className="mx-4 mb-4 p-3 rounded-lg bg-[var(--bg-subtle)] border border-[var(--border)]">
              <p className="text-[10px] text-[var(--fg-muted)] leading-relaxed">
                💡 <strong>Labels</strong> help you remember who owns what.
                Save a label, then export as <span className="font-mono">.jsonl</span> for portability (BIP-329 format).
              </p>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

function Detail({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <p className="text-[10px] text-[var(--fg-muted)] mb-0.5">{label}</p>
      <p className={`text-xs font-semibold text-[var(--fg)] ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  );
}
