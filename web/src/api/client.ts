import type { TxData, LabelPayload, HealthStatus, SessionData } from '../types/graph';

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts?.headers },
    ...opts,
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error ?? 'Request failed');
  return data as T;
}

// ── Node / status ──────────────────────────────────────────────────
export async function fetchStatus(): Promise<HealthStatus> {
  return req('/health');
}

// Kept for backwards compat (App.tsx probe uses this)
export const fetchHealth = fetchStatus;

// ── Transactions ───────────────────────────────────────────────────
export async function fetchTx(txid: string): Promise<{ ok: true; tx: TxData }> {
  return req(`/tx?txid=${txid}`);
}

// ── Address history ────────────────────────────────────────────────
export async function fetchAddressHistory(
  address: string,
  walletId = 'default',
): Promise<{ ok: true; address: string; history: { tx_hash: string; height: number; label: string | null }[]; count: number }> {
  return req(`/address?address=${encodeURIComponent(address)}&wallet_id=${walletId}`);
}

// ── Labels ─────────────────────────────────────────────────────────
export async function saveLabel(body: LabelPayload): Promise<{ ok: true }> {
  return req('/label', { method: 'POST', body: JSON.stringify(body) });
}

export async function deleteLabel(
  body: Pick<LabelPayload, 'ref_type' | 'ref' | 'wallet_id'>,
): Promise<{ ok: true }> {
  return req('/label', { method: 'DELETE', body: JSON.stringify(body) });
}

export async function fetchLabels(walletId = 'default') {
  return req<{ ok: true; labels: LabelPayload[]; count: number }>(
    `/labels?wallet_id=${walletId}`,
  );
}

// ── Wallets ────────────────────────────────────────────────────────
export async function fetchWallets(): Promise<{ ok: true; wallets: string[] }> {
  return req('/wallets');
}

// ── Sessions ───────────────────────────────────────────────────────
export async function fetchSessions(): Promise<{ ok: true; sessions: SessionData[] }> {
  return req('/sessions');
}

export async function createSession(
  rootTxid: string,
  walletIds: string[],
): Promise<{ ok: true; session_id: string; root_txid: string; wallet_ids: string[] }> {
  return req('/session', {
    method: 'POST',
    body: JSON.stringify({ root_txid: rootTxid, wallet_ids: walletIds }),
  });
}

// ── Import / Export ────────────────────────────────────────────────
export async function exportLabels(walletId = 'default') {
  const res = await fetch(`/api/labels/export?wallet_id=${walletId}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  a.download = `kycc-labels-${walletId}-${date}.jsonl`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function importLabels(file: File, walletId = 'default') {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch(`/api/labels/import?wallet_id=${walletId}`, {
    method: 'POST',
    body: fd,
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error ?? 'Import failed');
  return data as { ok: true; imported: number; wallet_id: string };
}
