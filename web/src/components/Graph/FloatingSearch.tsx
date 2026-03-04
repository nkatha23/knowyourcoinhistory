import { useState } from 'react';
import { Search, Loader2, X, Home } from 'lucide-react';
import { toast } from 'sonner';
import { fetchAddressHistory } from '../../api/client';
import { useGraphStore } from '../../store/graph';

const TXID_RE = /^[0-9a-fA-F]{64}$/;
const ADDR_RE = /^(1|3|bc1|tb1|bcrt1)/i;

interface AddrResult {
  tx_hash: string;
  height: number;
  label: string | null;
}

export default function FloatingSearch() {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [addrResults, setAddrResults] = useState<AddrResult[] | null>(null);

  const loadRootTx = useGraphStore((s) => s.loadRootTx);
  const clearGraph = useGraphStore((s) => s.clearGraph);
  const walletId = useGraphStore((s) => s.walletId);
  const backendOnline = useGraphStore((s) => s.backendOnline);

  async function handleSearch(e: { preventDefault(): void }) {
    e.preventDefault();
    const input = query.trim();
    if (!input) return;

    if (!backendOnline) {
      toast.error('Backend offline');
      return;
    }

    setSearching(true);
    setAddrResults(null);
    try {
      if (TXID_RE.test(input)) {
        await loadRootTx(input);
        toast.success('Transaction loaded');
        setQuery('');
      } else if (ADDR_RE.test(input)) {
        const result = await fetchAddressHistory(input, walletId);
        if (result.count === 0) {
          toast.info('No transactions found for this address');
        } else {
          setAddrResults(result.history);
        }
      } else {
        toast.error('Enter a 64-char txid or a Bitcoin address');
      }
    } catch (err: unknown) {
      toast.error(`Node error: ${err instanceof Error ? err.message : 'Failed'}`);
    } finally {
      setSearching(false);
    }
  }

  function handleClearText() {
    setQuery('');
    setAddrResults(null);
  }

  function handleClearGraph() {
    setQuery('');
    setAddrResults(null);
    clearGraph();
  }

  return (
    <div
      className="absolute top-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2"
      style={{ width: 'max-content' }}
    >
      <form onSubmit={handleSearch} className="relative" style={{ width: 400 }}>
        {/* Pill search bar */}
        <div
          className="flex items-center bg-[var(--bg)] border border-[var(--border)] shadow-lg overflow-hidden"
          style={{ height: 44, borderRadius: 22 }}
        >
          <Search size={15} className="ml-4 text-[var(--fg-muted)] shrink-0 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="txid or address…"
            className="flex-1 px-3 bg-transparent text-[var(--fg)] placeholder:text-[var(--fg-muted)] focus:outline-none font-mono"
            style={{ fontSize: 13 }}
          />
          {query && (
            <button
              type="button"
              onClick={handleClearText}
              className="text-[var(--fg-muted)] hover:text-[var(--fg)] mr-1 shrink-0"
            >
              <X size={14} />
            </button>
          )}
          <button
            type="submit"
            disabled={searching}
            className="shrink-0 h-full px-4 bg-[var(--color-btc)] text-white font-semibold hover:opacity-90 disabled:opacity-50 transition flex items-center gap-1.5"
            style={{ fontSize: 13, borderRadius: '0 20px 20px 0' }}
          >
            {searching && <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />}
            Search
          </button>
        </div>

        {/* Address results dropdown */}
        {addrResults && (
          <div
            className="absolute left-0 right-0 top-full mt-1.5 bg-[var(--bg)] border border-[var(--border)] shadow-xl z-20 overflow-y-auto"
            style={{ borderRadius: 12, maxHeight: 240 }}
          >
            <p className="text-xs text-[var(--fg-muted)] px-4 pt-3 pb-1">
              {addrResults.length} tx(s) found — pick one
            </p>
            {addrResults.map((tx) => (
              <button
                key={tx.tx_hash}
                type="button"
                onClick={() => {
                  loadRootTx(tx.tx_hash);
                  setAddrResults(null);
                  setQuery('');
                }}
                className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-[var(--bg-subtle)] transition text-left"
              >
                <span className="font-mono text-xs text-[var(--fg)]">
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

      {/* Home / clear graph button */}
      <button
        onClick={handleClearGraph}
        title="Clear graph — return to home"
        className="flex items-center justify-center bg-[var(--bg)] border border-[var(--border)] text-[var(--fg-muted)] hover:text-[var(--fg)] hover:border-[var(--color-btc)] shadow-lg transition shrink-0"
        style={{ width: 44, height: 44, borderRadius: '50%' }}
      >
        <Home size={16} />
      </button>
    </div>
  );
}
