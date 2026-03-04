import { useState } from 'react';
import { Search, Copy, Check, Loader2, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { fetchAddressHistory } from '../../api/client';
import { useGraphStore } from '../../store/graph';
import type { SessionData } from '../../types/graph';

const TXID_RE = /^[0-9a-fA-F]{64}$/;
const ADDR_RE = /^(1|3|bc1|tb1|bcrt1)/i;

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

const INFO_CARDS = [
  {
    icon: '🔍',
    title: 'What is a txid?',
    body: 'A transaction ID is a 64-character string that uniquely identifies any Bitcoin transaction',
  },
  {
    icon: '🔗',
    title: 'What is a UTXO?',
    body: 'An Unspent Transaction Output is a coin you can spend. Each input in a transaction consumes a previous UTXO',
  },
  {
    icon: '🏷️',
    title: 'What is BIP-329?',
    body: 'A standard format for attaching labels to your transactions and addresses, portable across wallets',
  },
];

interface AddrResult {
  tx_hash: string;
  height: number;
  label: string | null;
}

interface Props {
  onLoadTxid: (txid: string) => Promise<void>;
  recentSessions: SessionData[];
  backendOnline: boolean;
}

function fmtDate(ts: number) {
  return new Date(ts * 1000).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

export default function EmptyState({ onLoadTxid, recentSessions, backendOnline }: Props) {
  const walletId = useGraphStore((s) => s.walletId);
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [addrResults, setAddrResults] = useState<AddrResult[] | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [loadingTxid, setLoadingTxid] = useState<string | null>(null);

  async function handleSearch(e: { preventDefault(): void }) {
    e.preventDefault();
    const input = query.trim();
    if (!input) return;

    if (!backendOnline) {
      toast.error('Backend offline — start the server and configure a node in Settings');
      return;
    }

    setSearching(true);
    setAddrResults(null);
    try {
      if (TXID_RE.test(input)) {
        await onLoadTxid(input);
        toast.success('Transaction loaded');
      } else if (ADDR_RE.test(input)) {
        const result = await fetchAddressHistory(input, walletId);
        if (result.count === 0) {
          toast.info('No transactions found for this address');
        } else {
          setAddrResults(result.history);
        }
      } else {
        toast.error('Enter a 64-char txid or a Bitcoin address (1…, 3…, bc1…)');
      }
    } catch (err: unknown) {
      toast.error(`Node error: ${err instanceof Error ? err.message : 'Failed to load'}`);
    } finally {
      setSearching(false);
    }
  }

  async function loadTxid(txid: string) {
    setLoadingTxid(txid);
    try {
      await onLoadTxid(txid);
    } finally {
      setLoadingTxid(null);
      setAddrResults(null);
    }
  }

  function copy(txid: string) {
    navigator.clipboard.writeText(txid);
    setCopied(txid);
    setTimeout(() => setCopied(null), 1500);
  }

  return (
    <div className="absolute inset-0 flex items-start justify-center overflow-y-auto pointer-events-none">
      <div className="pointer-events-auto w-full text-center py-16 px-6" style={{ maxWidth: 760 }}>

        {/* Heading */}
        <h1
          className="text-[var(--fg)] mb-4"
          style={{ fontSize: 48, fontWeight: 700, fontFamily: 'IBM Plex Sans, sans-serif', lineHeight: 1.15 }}
        >
          Trace Your Coin History
        </h1>
        <p
          className="text-[var(--fg-muted)] mb-8 mx-auto leading-relaxed"
          style={{ fontSize: 18, maxWidth: 560 }}
        >
          Enter a Bitcoin transaction ID or address to visualise inputs, outputs, and privacy fingerprints
        </p>

        {/* Search box */}
        <form
          onSubmit={handleSearch}
          className="relative mx-auto mb-8"
          style={{ width: 600, maxWidth: '100%' }}
        >
          <div className="flex" style={{ height: 56, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Paste txid, outpoint (txid:vout), or address..."
              style={{
                flex: 1,
                height: 56,
                fontSize: 15,
                borderRadius: '12px 0 0 12px',
                border: '1px solid var(--border)',
                borderRight: 'none',
                paddingLeft: 20,
                paddingRight: 16,
                fontFamily: 'JetBrains Mono, monospace',
                background: 'var(--bg)',
                color: 'var(--fg)',
                outline: 'none',
                transition: 'border-color 0.15s, box-shadow 0.15s',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#f7931a';
                e.currentTarget.style.boxShadow = '0 0 0 2px rgba(247,147,26,0.25)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
            <button
              type="submit"
              disabled={searching}
              style={{
                height: 56,
                paddingLeft: 28,
                paddingRight: 28,
                borderRadius: '0 12px 12px 0',
                background: '#f7931a',
                color: 'white',
                fontSize: 16,
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                whiteSpace: 'nowrap',
                opacity: searching ? 0.7 : 1,
              }}
            >
              {searching
                ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                : <Search size={18} />}
              Search
            </button>
          </div>

          {/* Address results dropdown */}
          {addrResults && (
            <div
              className="absolute left-0 right-0 top-full mt-1 bg-[var(--bg)] border border-[var(--border)] shadow-xl z-20 overflow-y-auto text-left"
              style={{ borderRadius: 12, maxHeight: 240 }}
            >
              <p className="text-xs text-[var(--fg-muted)] px-4 pt-3 pb-1">
                {addrResults.length} transaction(s) found — select one to load
              </p>
              {addrResults.map((tx) => (
                <button
                  key={tx.tx_hash}
                  type="button"
                  onClick={() => loadTxid(tx.tx_hash)}
                  disabled={loadingTxid === tx.tx_hash}
                  className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-[var(--bg-subtle)] transition text-left disabled:opacity-60"
                >
                  <span className="font-mono text-sm text-[var(--fg)]">
                    {tx.tx_hash.slice(0, 14)}…{tx.tx_hash.slice(-8)}
                  </span>
                  <span className="text-xs text-[var(--fg-muted)]">
                    Block {tx.height || 'mempool'}
                  </span>
                </button>
              ))}
            </div>
          )}
        </form>

        {/* Info cards */}
        <div className="flex justify-center gap-4 mb-10 flex-wrap">
          {INFO_CARDS.map((card) => (
            <div
              key={card.title}
              className="text-left"
              style={{
                width: 180,
                background: 'var(--node-bg)',
                border: '1px solid var(--border)',
                borderRadius: 12,
                padding: 16,
                flexShrink: 0,
              }}
            >
              <div style={{ fontSize: 24, marginBottom: 10 }}>{card.icon}</div>
              <p
                className="text-[var(--fg)]"
                style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}
              >
                {card.title}
              </p>
              <p
                className="text-[var(--fg-muted)] leading-relaxed"
                style={{ fontSize: 13 }}
              >
                {card.body}
              </p>
            </div>
          ))}
        </div>

        {/* Famous transactions */}
        <div className="text-left mx-auto mb-8" style={{ maxWidth: 600 }}>
          <p
            className="text-[var(--fg-muted)] mb-3 uppercase tracking-wide"
            style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em' }}
          >
            Famous Transactions
            {!backendOnline && (
              <span className="normal-case font-normal ml-2 opacity-70">
                (copy txid — need mainnet node to load)
              </span>
            )}
          </p>
          <div className="space-y-2">
            {REFERENCE_TXS.map((tx) => (
              <div
                key={tx.txid}
                className="flex items-center justify-between px-4 py-3"
                style={{
                  border: '1px solid var(--border)',
                  borderRadius: 10,
                  background: 'var(--node-bg)',
                }}
              >
                <div>
                  <p className="text-[var(--fg)]" style={{ fontSize: 14, fontWeight: 600 }}>
                    {tx.label}
                  </p>
                  <p className="text-[var(--fg-muted)]" style={{ fontSize: 13 }}>
                    {tx.desc}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-4">
                  <button
                    onClick={() => copy(tx.txid)}
                    className="h-8 px-3 rounded-lg border border-[var(--border)] text-[var(--fg-muted)] hover:text-[var(--fg)] hover:border-[var(--color-btc)] transition flex items-center gap-1.5"
                    style={{ fontSize: 13 }}
                    title="Copy txid"
                  >
                    {copied === tx.txid
                      ? <Check size={14} className="text-green-500" />
                      : <Copy size={14} />}
                    Copy
                  </button>
                  <button
                    onClick={() => loadTxid(tx.txid)}
                    disabled={loadingTxid === tx.txid || !backendOnline}
                    className="h-8 px-3 rounded-lg bg-[var(--color-btc)] text-white font-semibold hover:opacity-90 disabled:opacity-50 transition"
                    style={{ fontSize: 13 }}
                  >
                    {loadingTxid === tx.txid ? '…' : 'Load'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent sessions */}
        {recentSessions.length > 0 && (
          <div className="text-left mx-auto" style={{ maxWidth: 600 }}>
            <p
              className="text-[var(--fg-muted)] mb-3 uppercase tracking-wide flex items-center gap-1.5"
              style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em' }}
            >
              <Clock size={12} /> Recent Sessions
            </p>
            <div className="space-y-2">
              {recentSessions.slice(0, 4).map((s) => (
                <button
                  key={s.session_id}
                  onClick={() => loadTxid(s.root_txid)}
                  disabled={loadingTxid === s.root_txid}
                  className="w-full flex items-center justify-between px-4 py-3 border border-[var(--border)] hover:border-[var(--color-btc)] transition text-left disabled:opacity-60"
                  style={{ borderRadius: 10, background: 'var(--node-bg)' }}
                >
                  <div>
                    <p className="font-mono text-[var(--fg)]" style={{ fontSize: 13 }}>
                      {s.root_txid.slice(0, 14)}…{s.root_txid.slice(-8)}
                    </p>
                    <p className="text-[var(--fg-muted)] mt-0.5" style={{ fontSize: 12 }}>
                      {fmtDate(s.created_at)} · {s.wallet_ids.join(', ')}
                    </p>
                  </div>
                  {loadingTxid === s.root_txid
                    ? <span className="w-4 h-4 border-2 border-[var(--color-btc)]/40 border-t-[var(--color-btc)] rounded-full animate-spin-slow" />
                    : <span className="text-[var(--fg-muted)]" style={{ fontSize: 13 }}>Resume →</span>
                  }
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
