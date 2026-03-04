import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { UTXONodeData } from '../../types/graph';
import { useGraphStore } from '../../store/graph';

const SCRIPT_BADGE: Record<string, string> = {
  p2wpkh:   'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
  p2tr:     'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
  p2pkh:    'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
  p2sh:     'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300',
  p2wsh:    'bg-teal-100 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300',
  coinbase:  'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400',
  op_return: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
  unknown:   'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
};

function btcDisplay(sats: number): string {
  if (sats === 0) return '0.00000000';
  return (sats / 1e8).toFixed(8);
}

function shortAddr(addr: string | null): string {
  if (!addr) return 'No address';
  if (addr.length <= 20) return addr;
  return `${addr.slice(0, 10)}…${addr.slice(-8)}`;
}

function UTXONode(props: NodeProps) {
  const { selected } = props;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = props.data as unknown as UTXONodeData;
  const expandInputTx = useGraphStore((s) => s.expandInputTx);

  const isCoinbase = data.script_type === 'coinbase';
  const isUnspent = !data.is_spent;

  // Border logic: unspent outputs get 3px green left border, coinbase gets gold, selected gets btc orange
  let borderColor = 'var(--node-border)';
  let borderLeftWidth = 1;
  if (isCoinbase) {
    borderColor = '#f59e0b';
    borderLeftWidth = 3;
  } else if (isUnspent && !data.isInput) {
    borderColor = '#22c55e';
    borderLeftWidth = 3;
  }
  if (selected) borderColor = 'var(--color-btc)';

  const scriptLabel = data.script_type.toUpperCase();

  return (
    <div
      className="border bg-[var(--node-bg)] text-[var(--fg)] relative"
      style={{
        width: 200,
        borderRadius: 20,
        borderColor,
        borderLeftWidth,
        // spent outputs get a slight grey tint
        opacity: data.isInput && data.is_spent ? 0.85 : 1,
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
          className="absolute -left-4 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-[var(--color-btc)] text-white flex items-center justify-center font-bold shadow-md hover:scale-110 transition-transform z-10"
          style={{ fontSize: 18 }}
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

      {/* Script badge row */}
      <div className="flex items-center justify-between px-3 pt-2.5 pb-0">
        <span
          className={`font-bold px-1.5 py-0.5 rounded-full ${SCRIPT_BADGE[data.script_type] ?? SCRIPT_BADGE.unknown}`}
          style={{ fontSize: 10 }}
        >
          {scriptLabel}
        </span>
        {isCoinbase && (
          <span className="text-amber-500" style={{ fontSize: 15 }} title="Coinbase">₿</span>
        )}
        {isUnspent && !data.isInput && (
          <span
            className="font-semibold text-green-600 dark:text-green-400"
            style={{ fontSize: 10 }}
          >
            UNSPENT
          </span>
        )}
      </div>

      {/* Value — 16px JetBrains Mono weight 700 */}
      <div className="px-3 pt-1.5 pb-0.5">
        <p
          className="font-mono text-[var(--fg)] leading-tight"
          style={{ fontSize: 16, fontWeight: 700 }}
        >
          {btcDisplay(data.value_sats)} BTC
        </p>
        {/* sats — 12px */}
        <p
          className="font-mono text-[var(--fg-muted)]"
          style={{ fontSize: 12 }}
        >
          {data.value_sats.toLocaleString()} sats
        </p>
      </div>

      {/* Address — 12px JetBrains Mono */}
      <div className="px-3 pb-2.5 pt-1">
        <p
          className="font-mono text-[var(--fg-muted)] truncate"
          style={{ fontSize: 12 }}
          title={data.address ?? undefined}
        >
          {shortAddr(data.address)}
        </p>
      </div>

      {/* Label */}
      {data.label && (
        <div className="mx-3 mb-2.5 px-2 py-1 rounded-md bg-[var(--color-btc-dim)] border border-[var(--color-btc)]/30">
          <p
            className="font-medium text-[var(--color-btc)] truncate"
            style={{ fontSize: 11 }}
          >
            🏷 {data.label}
          </p>
        </div>
      )}
    </div>
  );
}

export default memo(UTXONode);
