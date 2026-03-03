import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { UTXONodeData } from '../../types/graph';
import { useGraphStore } from '../../store/graph';

const SCRIPT_BADGE: Record<string, string> = {
  p2wpkh: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
  p2tr:    'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
  p2pkh:   'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
  p2sh:    'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300',
  p2wsh:   'bg-teal-100 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300',
  coinbase: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400',
  op_return: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
  unknown: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
};

function btcDisplay(sats: number): string {
  if (sats === 0) return '0';
  return (sats / 1e8).toFixed(sats >= 1_000_000 ? 4 : 6).replace(/\.?0+$/, '');
}

function shortAddr(addr: string | null): string {
  if (!addr) return 'No address';
  if (addr.length <= 20) return addr;
  return `${addr.slice(0, 8)}…${addr.slice(-6)}`;
}

function UTXONode(props: NodeProps) {
  const { selected } = props;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = props.data as unknown as UTXONodeData;
  const expandInputTx = useGraphStore((s) => s.expandInputTx);

  const isCoinbase = data.script_type === 'coinbase';
  const isUnspent = !data.is_spent;

  let borderColor = 'var(--node-border)';
  if (isCoinbase) borderColor = '#f59e0b';
  else if (isUnspent && !data.isInput) borderColor = '#22c55e';
  if (selected) borderColor = 'var(--color-btc)';

  const scriptLabel = data.script_type.toUpperCase();

  return (
    <div
      className="rounded-xl border bg-[var(--node-bg)] text-[var(--fg)] relative"
      style={{
        width: 200,
        borderColor,
        borderLeftWidth: !data.isInput && isUnspent ? 4 : 1,
        boxShadow: selected
          ? '0 0 0 2px var(--color-btc), var(--node-shadow)'
          : 'var(--node-shadow)',
      }}
    >
      {data.isInput && (
        <Handle
          type="source"
          position={Position.Right}
          style={{ background: '#9ca3af', border: 'none', width: 8, height: 8 }}
        />
      )}
      {!data.isInput && (
        <Handle
          type="target"
          position={Position.Left}
          style={{ background: '#9ca3af', border: 'none', width: 8, height: 8 }}
        />
      )}

      {/* Expand button — for inputs whose parent tx isn't loaded */}
      {data.isInput && data.canExpand && (
        <button
          className="absolute -left-4 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-[var(--color-btc)] text-white flex items-center justify-center text-sm font-bold shadow-md hover:scale-110 transition-transform z-10"
          title="Load parent transaction"
          onClick={(e) => {
            e.stopPropagation();
            expandInputTx(data.txid, data.vout);
          }}
        >
          {data.parentTxLoading ? (
            <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin-slow" />
          ) : (
            '+'
          )}
        </button>
      )}

      {/* Script badge + coinbase crown */}
      <div className="flex items-center justify-between px-3 pt-2.5 pb-0">
        <span
          className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${SCRIPT_BADGE[data.script_type] ?? SCRIPT_BADGE.unknown}`}
        >
          {scriptLabel}
        </span>
        {isCoinbase && <span className="text-amber-500 text-sm" title="Coinbase">₿</span>}
        {isUnspent && !data.isInput && (
          <span className="text-[9px] font-semibold text-green-600 dark:text-green-400">UNSPENT</span>
        )}
      </div>

      {/* Value */}
      <div className="px-3 pt-1.5 pb-0.5">
        <p className="font-mono font-semibold text-base leading-tight text-[var(--fg)]">
          {btcDisplay(data.value_sats)} BTC
        </p>
        <p className="font-mono text-[10px] text-[var(--fg-muted)]">
          {data.value_sats.toLocaleString()} sats
        </p>
      </div>

      {/* Address */}
      <div className="px-3 pb-2.5 pt-1">
        <p
          className="font-mono text-[10px] text-[var(--fg-muted)] truncate"
          title={data.address ?? undefined}
        >
          {shortAddr(data.address)}
        </p>
      </div>

      {/* Label */}
      {data.label && (
        <div className="mx-3 mb-2.5 px-2 py-1 rounded-md bg-[var(--color-btc-dim)] border border-[var(--color-btc)]/30">
          <p className="text-[10px] font-medium text-[var(--color-btc)] truncate">🏷 {data.label}</p>
        </div>
      )}
    </div>
  );
}

export default memo(UTXONode);
