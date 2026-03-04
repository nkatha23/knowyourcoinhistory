# Architecture

## Overview

```
Browser (React 19 + React Flow v12)
        │  HTTP/JSON  (Vite dev proxy → localhost:5050)
        │
Flask API Server  (Python 3.11+, port 5050)
        │
   NodeAdapter ABC
   ┌────┴────┐
Bitcoin Core   Electrum Server
 JSON-RPC       TCP/SSL JSON-RPC
 (port 8332 / 18443 regtest)
```

KYCC is intentionally local-first: the Flask process never makes outbound calls to any third-party service. All network traffic goes to the configured Bitcoin node on localhost (or LAN).

---

## Backend Components

### `kycc/config.py` — Config loader

Reads `kycc.toml` at startup using Python's built-in `tomllib`. Exposes a `Config` dataclass consumed by `server.py`.

Key fields:
- `node_type` — `"bitcoincore"` or `"electrum"`
- `node_host`, `node_port`, `node_user`, `node_password`
- `node_network` — `"mainnet"` | `"testnet"` | `"signet"` | `"regtest"`
- `server_host`, `server_port`, `server_debug`
- `db_path` — SQLite file path for the label store

### `kycc/adapters/` — Node adapters

Abstract base (`NodeAdapter`) defines three methods every adapter must implement:

```python
def get_raw_transaction(self, txid: str) -> dict
def get_block_height(self) -> int
def get_address_history(self, address: str) -> list[dict]
```

**`BitcoinCoreAdapter`** (`bitcoincore.py`)

Uses `python-bitcoinrpc`'s `AuthServiceProxy`. Key design decision: a **fresh `AuthServiceProxy` is created on every RPC call** rather than reusing one instance. This avoids `CannotSendRequest` errors that occur when `http.client.HTTPConnection` (used internally by `AuthServiceProxy`) enters a stale/half-sent state after a failed or interrupted prior request.

```python
def _rpc(self) -> AuthServiceProxy:
    """Fresh proxy per call — avoids CannotSendRequest on stale connections."""
    return AuthServiceProxy(self._url)
```

**`ElectrumAdapter`** (`electrum.py`)

Connects to an Electrum server via TCP JSON-RPC. Translates `blockchain.transaction.get` and `blockchain.scripthash.get_history` calls into the same `NodeAdapter` interface.

### `kycc/graph/` — Transaction graph

**`parser.py`** — `parse_tx(raw) -> TxNode`

Converts the output of `getrawtransaction(txid, verbose=2)` into a `TxNode` dataclass. `verbose=2` resolves `prevout` data inline so no additional RPC call is needed per input.

Critical implementation note: `python-bitcoinrpc` returns BTC amounts as `decimal.Decimal` (not `float`) to avoid precision loss. All satoshi conversions use integer multiplication:

```python
sats = round(value * 100_000_000)  # NOT value * 1e8 (float — raises TypeError)
```

**`models.py`** — Dataclasses: `TxNode`, `UTXONode`

**`serializer.py`** — `tx_to_dict(tx) -> dict` — converts `TxNode` to the JSON structure the frontend consumes.

### `kycc/fingerprint/` — Privacy heuristics

`FingerprintEngine` runs all enabled detectors over a `TxNode` and attaches `Annotation` objects. Each annotation has:
- `code` — machine-readable identifier (e.g. `"UIOH"`, `"ADDRESS_REUSE"`)
- `severity` — `"info"` | `"warning"` | `"flag"`
- `description` — human-readable explanation
- `affected` — list of addresses or outpoints involved

See [HEURISTICS.md](HEURISTICS.md) for full detector documentation.

### `kycc/labels/` — BIP-329 label store

SQLite-backed. Schema:
```sql
CREATE TABLE labels (
    wallet_id   TEXT NOT NULL,
    ref_type    TEXT NOT NULL,   -- tx | utxo | addr | xpub
    ref         TEXT NOT NULL,
    label       TEXT NOT NULL,
    origin      TEXT,
    spendable   INTEGER,
    created_at  INTEGER,
    updated_at  INTEGER,
    PRIMARY KEY (wallet_id, ref_type, ref)
);
```

Labels are wallet-namespaced so multiple wallets can coexist without collision. `bip329.py` serialises rows to/from the JSONL format defined in BIP-329.

### `kycc/routes/` — Flask API blueprints

Each route module is a separate `Blueprint` registered in `server.py`. See the [API reference in README.md](../README.md#api-reference) for the full endpoint list.

---

## Frontend Components

### State — `store/graph.ts`

Zustand store is the single source of truth for:
- `nodes`, `edges` — React Flow graph data
- `selectedId` — currently selected node ID
- `theme` — `'light'` | `'dark'` (persisted to `localStorage`)
- `fingerprintEnabled` — show/hide annotation overlays
- `hiddenHeuristics` — set of disabled heuristic keys (persisted)
- `walletId` — current wallet context (persisted)
- `backendOnline` — backend connectivity flag
- `loadedTxIds`, `loadingTxIds` — prevent duplicate fetches
- `recentSessions` — loaded from `/api/sessions` on startup

Key actions:
- `loadRootTx(txid)` — fetches TX, builds nodes/edges, replaces graph
- `expandInputTx(txid, vout)` — fetches parent TX, merges into existing graph
- `clearGraph()` — resets to empty state

### Graph layout

Manual positioning (no auto-layout library):
- Transaction node at `(CANVAS_CX, CANVAS_CY)` = `(500, 300)`
- Input UTXOs at `tx.x − 420px`, vertically centred with `ROW_GAP = 110px`
- Output UTXOs at `tx.x + 420px`, same vertical logic
- Expanding a parent TX places it `420px` left of the clicked input UTXO

Edges carry BTC/sat value labels rendered at the midpoint via React Flow's built-in `label` prop.

### Component hierarchy

```
App
├── Toolbar              Logo, wallet, fingerprint toggle, import/export, settings
├── GraphCanvas          React Flow wrapper
│   ├── TransactionNode  280px card, orange top border, fingerprint dots
│   ├── UTXONode         200px pill, green/gold/grey borders by state
│   ├── EmptyState       Hero landing (when nodes = 0)
│   └── FloatingSearch   Pill search bar (when nodes > 0)
├── RightPanel           Label editor + annotation detail (spring slide-in)
└── SettingsModal        Node status + heuristic toggles (framer-motion dialog)
```

### Search flow

**Landing page (EmptyState)**
1. User enters a 64-hex txid → `GET /api/tx?txid=` → graph renders
2. User enters a Bitcoin address → `GET /api/address?address=` → dropdown of matching txids → user picks one → graph renders
3. Error response → red toast `"Node error: {message}"`

**Floating search bar (FloatingSearch — visible when graph is loaded)**
- Same logic as above but in a compact 400px pill at top-center of canvas
- Home button (⌂) clears the graph and returns to the landing page
- Address dropdown appears below the pill

### Dark mode

Class-based: `.dark` on `<html>`. All colours are CSS custom properties (`--bg`, `--fg`, `--border`, `--node-bg`, etc.) defined in `index.css` for both modes. Tailwind v4's `@custom-variant dark` makes `dark:` utility classes target `.dark *`.

---

## CI Pipeline

`.github/workflows/ci.yml` runs on every push to `dev` and `main`:

1. `ruff check kycc/ tests/` — import sorting, unused imports
2. `black --check kycc/ tests/` — formatting
3. `pytest tests/unit/ --cov=kycc --cov-fail-under=80` — unit tests + 80% coverage gate

Matrix: Python 3.11 and 3.12. Integration tests (`tests/integration/`) are skipped in CI because they require a live Bitcoin node.

---

## Known Limitations

- `loadedTxIds` in the Zustand store accumulates across root TX loads (not cleared when loading a new root). This means expand buttons may not appear on inputs whose parent TXIDs happen to match ones loaded in a previous graph. Workaround: use the Home button to clear the graph before starting a new search.
- Address history uses `scantxoutset` (Bitcoin Core) which only finds UTXOs in the current UTXO set — it cannot find spent outputs.
- The Electrum adapter does not implement `get_raw_transaction` for transactions not in the address history; full graph traversal requires Bitcoin Core with `txindex=1`.
