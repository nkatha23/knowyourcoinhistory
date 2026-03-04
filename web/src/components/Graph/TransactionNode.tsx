import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { TxNodeData, Severity } from '../../types/graph';
import { useGraphStore, ANNOTATION_TO_KEY } from '../../store/graph';

const SEV_DOT: Record<Severity, string> = {
  info: 'bg-blue-500',
  warning: 'bg-amber-500',
  flag: 'bg-red-500',
};

const SEV_LABEL: Record<Severity, string> = {
  info: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 border-blue-200 dark:border-blue-800',
  warning: 'text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/60 border-amber-200 dark:border-amber-800',
  flag: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/60 border-red-200 dark:border-red-800',
};

function fmt(sats: number | null): string {
  if (sats === null) return '—';
  if (sats >= 1_000_000) return `${(sats / 1e8).toFixed(4)} BTC`;
  return `${sats.toLocaleString()} sats`;
}

function short(txid: string): string {
  return `${txid.slice(0, 8)}…${txid.slice(-8)}`;
}

function TransactionNode(props: NodeProps) {
  const { selected } = props;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = props.data as unknown as TxNodeData;
  const fingerprintEnabled = useGraphStore((s) => s.fingerprintEnabled);
  const hiddenHeuristics = useGraphStore((s) => s.hiddenHeuristics);
  const annotations = fingerprintEnabled
    ? data.annotations.filter((a) => {
        const key = ANNOTATION_TO_KEY[a.code];
        return !key || !hiddenHeuristics.has(key);
      })
    : [];

  return (
    <div
      className="rounded-lg border bg-[var(--node-bg)] text-[var(--fg)]"
      style={{
        width: 280,
        borderColor: selected ? 'var(--color-btc)' : 'var(--node-border)',
        borderTopWidth: 4,
        borderTopColor: 'var(--color-btc)',
        boxShadow: selected
          ? '0 0 0 2px var(--color-btc), var(--node-shadow)'
          : 'var(--node-shadow)',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: '#9ca3af', border: 'none', width: 8, height: 8 }} />

      {/* Header */}
      <div className="px-3 pt-3 pb-2">
        <div className="flex items-center gap-1.5 mb-1.5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--fg-muted)]">
            Transaction
          </span>
          {data.is_coinbase && (
            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-700">
              COINBASE
            </span>
          )}
          {data.is_rbf && (
            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
              RBF
            </span>
          )}
        </div>
        {/* txid: 14px JetBrains Mono weight 600 */}
        <p
          className="font-mono text-[var(--fg)] truncate"
          style={{ fontSize: 14, fontWeight: 600 }}
          title={data.txid}
        >
          {short(data.txid)}
        </p>
      </div>

      {/* Metadata chips — 12px */}
      <div className="px-3 pb-2 flex flex-wrap gap-1.5">
        {data.fee_sats !== null && (
          <Chip label="Fee" value={fmt(data.fee_sats)} />
        )}
        {data.block_height !== null && (
          <Chip label="Block" value={data.block_height.toLocaleString()} />
        )}
        <Chip label="v" value={String(data.version)} />
        {data.size > 0 && <Chip label="vB" value={String(Math.ceil(data.weight / 4))} />}
      </div>

      {/* I/O summary */}
      <div className="mx-3 mb-2 px-2 py-1.5 rounded-md bg-[var(--bg-subtle)] border border-[var(--border)] flex justify-around text-center">
        <div>
          <p className="text-[var(--fg-muted)] mb-0.5" style={{ fontSize: 11 }}>Inputs</p>
          <p className="font-semibold" style={{ fontSize: 14 }}>{data.inputs.length}</p>
        </div>
        <div className="border-l border-[var(--border)]" />
        <div>
          <p className="text-[var(--fg-muted)] mb-0.5" style={{ fontSize: 11 }}>Outputs</p>
          <p className="font-semibold" style={{ fontSize: 14 }}>{data.outputs.length}</p>
        </div>
        <div className="border-l border-[var(--border)]" />
        <div>
          <p className="text-[var(--fg-muted)] mb-0.5" style={{ fontSize: 11 }}>Total in</p>
          <p className="font-semibold font-mono" style={{ fontSize: 13 }}>
            {fmt(data.inputs.reduce((s, u) => s + u.value_sats, 0))}
          </p>
        </div>
      </div>

      {/* Label */}
      {data.label && (
        <div className="mx-3 mb-2 px-2 py-1 rounded-md bg-[var(--color-btc-dim)] border border-[var(--color-btc)]/30">
          <p className="font-medium text-[var(--color-btc)] truncate" style={{ fontSize: 13 }}>
            🏷 {data.label}
          </p>
        </div>
      )}

      {/* Fingerprint annotations */}
      {annotations.length > 0 && (
        <div className="px-3 pb-3 space-y-1">
          {annotations.map((a, i) => (
            <div
              key={i}
              className={`flex items-start gap-2 px-2 py-1.5 rounded-md border ${SEV_LABEL[a.severity]}`}
            >
              <span className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${SEV_DOT[a.severity]}`} />
              <div>
                <p className="font-mono font-semibold" style={{ fontSize: 11 }}>{a.code}</p>
                <p className="font-sans opacity-80 leading-tight mt-0.5" style={{ fontSize: 11 }}>{a.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <Handle type="source" position={Position.Right} style={{ background: '#9ca3af', border: 'none', width: 8, height: 8 }} />
    </div>
  );
}

function Chip({ label, value }: { label: string; value: string }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-[var(--border)] bg-[var(--bg-subtle)] text-[var(--fg-muted)]"
      style={{ fontSize: 12 }}
    >
      <span className="font-medium text-[var(--fg-muted)]">{label}</span>
      <span className="font-mono font-semibold text-[var(--fg)]">{value}</span>
    </span>
  );
}

export default memo(TransactionNode);
