import { useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, Copy, Check } from 'lucide-react';
import type { SessionData } from '../../types/graph';

interface Props {
  onLoadTxid: (txid: string) => Promise<void>;
  recentSessions: SessionData[];
  backendOnline: boolean;
}

// Famous Bitcoin transactions — real mainnet txids for reference.
// These load only if you have a mainnet node; otherwise use them as copy references.
const REFERENCE_TXS = [
  {
    txid: 'f4184fc596403b9d638783cf57adfe4c75c605f6356fbc91338530e9831e9e16',
    label: 'First BTC payment',
    desc: 'Satoshi → Hal Finney, 10 BTC, block 170',
  },
  {
    txid: 'a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d',
    label: 'Bitcoin Pizza',
    desc: '10,000 BTC for two pizzas — block 57,043',
  },
];

function shortTxid(txid: string) {
  return `${txid.slice(0, 10)}…${txid.slice(-8)}`;
}

function fmtDate(ts: number) {
  return new Date(ts * 1000).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function EmptyState({ onLoadTxid, recentSessions, backendOnline }: Props) {
  const [loadingTxid, setLoadingTxid] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  async function load(txid: string) {
    setLoadingTxid(txid);
    try { await onLoadTxid(txid); } finally { setLoadingTxid(null); }
  }

  function copy(txid: string) {
    navigator.clipboard.writeText(txid);
    setCopied(txid);
    setTimeout(() => setCopied(null), 1500);
  }

  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <motion.div
        className="pointer-events-auto text-center px-6 max-w-lg w-full"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        {/* Icon */}
        <div className="animate-coin-pulse inline-flex items-center justify-center w-14 h-14 rounded-full bg-orange-100 dark:bg-orange-950/50 text-2xl mb-4 border-2 border-[var(--color-btc)]/30">
          ₿
        </div>

        <h2 className="text-xl font-bold mb-2 text-[var(--fg)]">Trace Your Coin History</h2>
        <p className="text-sm text-[var(--fg-muted)] leading-relaxed mb-1">
          Search a <strong>transaction ID</strong> or <strong>Bitcoin address</strong> in the bar above
          to visualise inputs, outputs, and privacy fingerprints.
        </p>
        <p className="text-xs text-[var(--fg-muted)] mb-5">
          Click{' '}
          <span className="font-mono bg-[var(--bg-subtle)] border border-[var(--border)] px-1.5 py-0.5 rounded text-[var(--color-btc)] font-bold">
            +
          </span>{' '}
          on any input UTXO to load its parent transaction and trace the coin further back.
        </p>

        {/* Recent sessions */}
        {recentSessions.length > 0 && (
          <div className="mb-5 text-left">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--fg-muted)] mb-2 flex items-center gap-1.5">
              <Clock className="w-3 h-3" /> Recent sessions
            </p>
            <div className="space-y-1.5">
              {recentSessions.slice(0, 4).map((s) => (
                <button
                  key={s.session_id}
                  onClick={() => load(s.root_txid)}
                  disabled={loadingTxid === s.root_txid}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--node-bg)] hover:border-[var(--color-btc)] hover:bg-orange-50 dark:hover:bg-orange-950/20 transition group text-left disabled:opacity-60"
                >
                  <div>
                    <p className="font-mono text-xs text-[var(--fg)] group-hover:text-[var(--color-btc)] transition-colors">
                      {shortTxid(s.root_txid)}
                    </p>
                    <p className="text-[10px] text-[var(--fg-muted)] mt-0.5">
                      {fmtDate(s.created_at)} · wallet: {s.wallet_ids.join(', ')}
                    </p>
                  </div>
                  {loadingTxid === s.root_txid
                    ? <span className="w-4 h-4 border-2 border-[var(--color-btc)]/40 border-t-[var(--color-btc)] rounded-full animate-spin-slow" />
                    : <span className="text-[10px] text-[var(--fg-muted)] group-hover:text-[var(--color-btc)]">Resume →</span>
                  }
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Reference transactions */}
        <div className="mb-5 text-left">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--fg-muted)] mb-2">
            Famous transactions {!backendOnline && <span className="normal-case font-normal">(copy txid, connect a mainnet node to load)</span>}
          </p>
          <div className="space-y-1.5">
            {REFERENCE_TXS.map((tx) => (
              <div
                key={tx.txid}
                className="flex items-center justify-between px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--node-bg)] gap-3"
              >
                <div className="min-w-0">
                  <p className="font-semibold text-xs text-[var(--fg)]">{tx.label}</p>
                  <p className="text-[10px] text-[var(--fg-muted)]">{tx.desc}</p>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => copy(tx.txid)}
                    className="h-7 px-2 rounded-md border border-[var(--border)] text-[var(--fg-muted)] hover:text-[var(--fg)] hover:border-[var(--color-btc)] transition flex items-center gap-1 text-[10px]"
                    title="Copy txid"
                  >
                    {copied === tx.txid
                      ? <><Check className="w-3 h-3 text-green-500" /> Copied</>
                      : <><Copy className="w-3 h-3" /> Copy</>}
                  </button>
                  {backendOnline && (
                    <button
                      onClick={() => load(tx.txid)}
                      disabled={loadingTxid === tx.txid}
                      className="h-7 px-2 rounded-md bg-[var(--color-btc)] text-white text-[10px] font-semibold hover:opacity-90 disabled:opacity-50 transition"
                    >
                      {loadingTxid === tx.txid ? '…' : 'Load'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* What is KYCC */}
        <div className="p-3 rounded-lg bg-[var(--bg-subtle)] border border-[var(--border)] text-left">
          <p className="text-xs font-semibold text-[var(--fg)] mb-1">💡 What is KYCC?</p>
          <p className="text-xs text-[var(--fg-muted)] leading-relaxed">
            Know Your Coin History analyses Bitcoin transactions for privacy patterns and lets you label
            inputs/outputs with wallet context — then export as <span className="font-mono">BIP-329</span>.
            Requires a local Bitcoin Core or Electrum node. No external API calls.
          </p>
        </div>
      </motion.div>
    </div>
  );
}
