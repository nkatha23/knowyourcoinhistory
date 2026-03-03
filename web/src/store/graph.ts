import { create } from 'zustand';
import type { Node, Edge, XYPosition } from '@xyflow/react';
import type { TxData, AppNodeData, TxNodeData, UTXONodeData, SessionData } from '../types/graph';
import { fetchTx, createSession } from '../api/client';

// ── Layout constants ──────────────────────────────────────────────
const UTXO_OFFSET = 420;
const ROW_GAP = 110;
const CANVAS_CX = 500;
const CANVAS_CY = 300;

// ── Annotation code → heuristic config key map ────────────────────
export const ANNOTATION_TO_KEY: Record<string, string> = {
  RBF_SIGNALING:       'rbf',
  ANTI_FEE_SNIPING:    'locktime',
  TIMELOCK_UNIX:       'locktime',
  ADDRESS_REUSE:       'address_reuse',
  ROUND_PAYMENT:       'round_payment',
  PROBABLE_CHANGE:     'change_inference',
  SCRIPT_TYPE_MISMATCH:'script_mismatch',
  CONSOLIDATION:       'consolidation',
  UIOH:                'uioh',
};

// ── localStorage persistence ──────────────────────────────────────
function persist<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
}
function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw !== null ? (JSON.parse(raw) as T) : fallback;
  } catch { return fallback; }
}

const storedTheme = load<'light' | 'dark'>('kycc:theme', 'light');
const storedWalletId = load<string>('kycc:walletId', 'default');
const storedHidden = load<string[]>('kycc:hiddenHeuristics', []);

// Apply stored theme immediately
if (storedTheme === 'dark') document.documentElement.classList.add('dark');

// ── Helpers ───────────────────────────────────────────────────────
function utxoNodeId(txid: string, vout: number) { return `utxo-${txid}-${vout}`; }
function txNodeId(txid: string) { return `tx-${txid}`; }

function centerY(count: number, index: number, cy: number): number {
  const total = (count - 1) * ROW_GAP;
  return cy - total / 2 + index * ROW_GAP;
}

function buildNodes(
  tx: TxData,
  txPos: XYPosition,
  loadedTxIds: Set<string>,
): { nodes: Node<AppNodeData>[]; edges: Edge[] } {
  const nodes: Node<AppNodeData>[] = [];
  const edges: Edge[] = [];

  const txId = txNodeId(tx.txid);
  nodes.push({
    id: txId,
    type: 'txNode',
    position: txPos,
    data: { kind: 'tx', ...tx } as TxNodeData,
    draggable: true,
  });

  tx.inputs.forEach((u, i) => {
    const uid = utxoNodeId(u.txid, u.vout);
    const isCoinbase = u.script_type === 'coinbase';
    nodes.push({
      id: uid,
      type: 'utxoNode',
      position: { x: txPos.x - UTXO_OFFSET, y: centerY(tx.inputs.length, i, txPos.y) },
      data: { kind: 'utxo', ...u, isInput: true, canExpand: !isCoinbase && !loadedTxIds.has(u.txid) } as UTXONodeData,
      draggable: true,
    });
    edges.push({ id: `e-${uid}-${txId}`, source: uid, target: txId, animated: true, type: 'smoothstep' });
  });

  tx.outputs.forEach((u, i) => {
    const uid = utxoNodeId(tx.txid, u.vout);
    nodes.push({
      id: uid,
      type: 'utxoNode',
      position: { x: txPos.x + UTXO_OFFSET, y: centerY(tx.outputs.length, i, txPos.y) },
      data: { kind: 'utxo', ...u, isInput: false, canExpand: false } as UTXONodeData,
      draggable: true,
    });
    edges.push({ id: `e-${txId}-${uid}`, source: txId, target: uid, animated: true, type: 'smoothstep' });
  });

  return { nodes, edges };
}

// ── Store ─────────────────────────────────────────────────────────
interface AppStore {
  nodes: Node<AppNodeData>[];
  edges: Edge[];
  selectedId: string | null;
  theme: 'light' | 'dark';
  fingerprintEnabled: boolean;
  hiddenHeuristics: Set<string>;
  walletId: string;
  backendOnline: boolean;
  loadedTxIds: Set<string>;
  loadingTxIds: Set<string>;
  currentSessionId: string | null;
  recentSessions: SessionData[];

  setNodes: (nodes: Node<AppNodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  selectNode: (id: string | null) => void;
  toggleTheme: () => void;
  toggleFingerprint: () => void;
  setHiddenHeuristics: (keys: Set<string>) => void;
  setWalletId: (id: string) => void;
  setBackendOnline: (v: boolean) => void;
  setRecentSessions: (sessions: SessionData[]) => void;

  loadRootTx: (txid: string) => Promise<void>;
  expandInputTx: (inputTxid: string, inputVout: number) => Promise<void>;
  clearGraph: () => void;
  refreshNodeLabel: (nodeId: string, label: string | null) => void;
}

export const useGraphStore = create<AppStore>((set, get) => ({
  nodes: [],
  edges: [],
  selectedId: null,
  theme: storedTheme,
  fingerprintEnabled: true,
  hiddenHeuristics: new Set(storedHidden),
  walletId: storedWalletId,
  backendOnline: false,
  loadedTxIds: new Set(),
  loadingTxIds: new Set(),
  currentSessionId: null,
  recentSessions: [],

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  selectNode: (id) => set({ selectedId: id }),

  toggleTheme: () =>
    set((s) => {
      const next = s.theme === 'light' ? 'dark' : 'light';
      document.documentElement.classList.toggle('dark', next === 'dark');
      persist('kycc:theme', next);
      return { theme: next };
    }),

  toggleFingerprint: () =>
    set((s) => ({ fingerprintEnabled: !s.fingerprintEnabled })),

  setHiddenHeuristics: (keys) => {
    persist('kycc:hiddenHeuristics', [...keys]);
    set({ hiddenHeuristics: keys });
  },

  setWalletId: (id) => {
    persist('kycc:walletId', id);
    set({ walletId: id });
  },

  setBackendOnline: (v) => set({ backendOnline: v }),
  setRecentSessions: (sessions) => set({ recentSessions: sessions }),

  loadRootTx: async (txid) => {
    const { loadedTxIds, loadingTxIds, walletId } = get();
    if (loadedTxIds.has(txid) || loadingTxIds.has(txid)) return;

    set((s) => {
      const next = new Set(s.loadingTxIds);
      next.add(txid);
      return { loadingTxIds: next };
    });

    const tx = await fetchTx(txid).then((r) => r.tx);
    const { nodes: newNodes, edges: newEdges } = buildNodes(
      tx,
      { x: CANVAS_CX, y: CANVAS_CY },
      new Set([txid]),
    );

    set((s) => {
      const loaded = new Set(s.loadedTxIds);
      loaded.add(txid);
      const loading = new Set(s.loadingTxIds);
      loading.delete(txid);
      return { nodes: newNodes, edges: newEdges, loadedTxIds: loaded, loadingTxIds: loading };
    });

    // Create a session for this root tx (fire-and-forget)
    if (get().currentSessionId === null) {
      createSession(txid, [walletId])
        .then((r) => set({ currentSessionId: r.session_id }))
        .catch(() => {/* session creation is optional */});
    }
  },

  expandInputTx: async (inputTxid, inputVout) => {
    const { loadedTxIds, loadingTxIds, nodes } = get();
    if (loadedTxIds.has(inputTxid) || loadingTxIds.has(inputTxid)) return;

    set((s) => ({
      loadingTxIds: new Set([...s.loadingTxIds, inputTxid]),
      nodes: s.nodes.map((n) =>
        n.id === utxoNodeId(inputTxid, inputVout)
          ? { ...n, data: { ...n.data, parentTxLoading: true } as AppNodeData }
          : n,
      ),
    }));

    const tx = await fetchTx(inputTxid).then((r) => r.tx);

    const existingUtxo = nodes.find((n) => n.id === utxoNodeId(inputTxid, inputVout));
    const utxoX = existingUtxo?.position.x ?? CANVAS_CX - UTXO_OFFSET;
    const utxoY = existingUtxo?.position.y ?? CANVAS_CY;

    const nextLoaded = new Set([...loadedTxIds, inputTxid]);
    const { nodes: newNodes, edges: newEdges } = buildNodes(
      tx,
      { x: utxoX - UTXO_OFFSET, y: utxoY },
      nextLoaded,
    );

    set((s) => {
      const loaded = new Set([...s.loadedTxIds, inputTxid]);
      const loading = new Set(s.loadingTxIds);
      loading.delete(inputTxid);

      const existingIds = new Set(s.nodes.map((n) => n.id));
      const existingEdgeIds = new Set(s.edges.map((e) => e.id));

      const updatedExisting = s.nodes.map((n) =>
        n.id === utxoNodeId(inputTxid, inputVout)
          ? { ...n, data: { ...n.data, canExpand: false, parentTxLoading: false } as AppNodeData }
          : n,
      );

      return {
        nodes: [...updatedExisting, ...newNodes.filter((n) => !existingIds.has(n.id))],
        edges: [...s.edges, ...newEdges.filter((e) => !existingEdgeIds.has(e.id))],
        loadedTxIds: loaded,
        loadingTxIds: loading,
      };
    });
  },

  clearGraph: () =>
    set({ nodes: [], edges: [], loadedTxIds: new Set(), selectedId: null, currentSessionId: null }),

  refreshNodeLabel: (nodeId, label) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, label } as AppNodeData } : n,
      ),
    })),
}));
