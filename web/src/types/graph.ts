export type ScriptType =
  | 'p2pkh'
  | 'p2sh'
  | 'p2wpkh'
  | 'p2wsh'
  | 'p2tr'
  | 'p2sh-p2wpkh'
  | 'coinbase'
  | 'op_return'
  | 'unknown';

export type Severity = 'info' | 'warning' | 'flag';
export type RefType = 'tx' | 'utxo' | 'addr' | 'xpub';

export interface Annotation {
  code: string;
  severity: Severity;
  description: string;
  affected: string[];
}

export interface UTXOData {
  txid: string;
  vout: number;
  value_sats: number;
  value_btc: number;
  script_pubkey_hex: string;
  script_type: ScriptType;
  address: string | null;
  is_spent: boolean;
  spending_txid: string | null;
  label: string | null;
}

export interface TxData {
  txid: string;
  block_height: number | null;
  block_hash: string | null;
  fee_sats: number | null;
  fee_btc: number | null;
  is_coinbase: boolean;
  is_rbf: boolean;
  locktime: number;
  locktime_type: string;
  version: number;
  size: number;
  weight: number;
  inputs: UTXOData[];
  outputs: UTXOData[];
  label: string | null;
  annotations: Annotation[];
}

export interface LabelPayload {
  ref_type: RefType;
  ref: string;
  label: string;
  wallet_id?: string;
  spendable?: boolean;
}

export interface SessionData {
  session_id: string;
  root_txid: string;
  wallet_ids: string[];
  created_at: number;
}

export interface HeuristicMeta {
  key: string;
  display: string;
  codes: string[];
  desc: string;
  enabled: boolean;
}

export interface HealthStatus {
  ok: true;
  version: string;
  node_type: string;
  network: string;
  node_host: string;
  node_port: number;
  block_height: number | null;
  node_online: boolean;
  heuristics: HeuristicMeta[];
}

// React Flow node data — index signature required by @xyflow/react v12
export interface TxNodeData extends TxData {
  kind: 'tx';
  [key: string]: unknown;
}

export interface UTXONodeData extends UTXOData {
  kind: 'utxo';
  isInput: boolean;
  canExpand: boolean;
  parentTxLoading?: boolean;
  [key: string]: unknown;
}

export type AppNodeData = TxNodeData | UTXONodeData;
