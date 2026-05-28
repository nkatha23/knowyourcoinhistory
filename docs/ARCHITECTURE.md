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

Reads `kycc.toml` using Python's built-in `tomllib`, then overlays environment variables. Exposes a `Config` dataclass consumed by `server.py`.

Priority: **env var > kycc.toml > built-in default**. `kycc.toml` is optional — all values can be supplied via env vars, which is the recommended approach for Docker deployments.

Key fields:
- `node_type` — `"bitcoincore"` or `"electrum"`
- `node_host`, `node_port`, `node_user`, `node_password`
- `node_network` — `"mainnet"` | `"testnet"` | `"signet"` | `"regtest"`
- `server_host`, `server_port`, `server_debug`
- `db_path` — SQLite file path for the label store (defaults to `kycc.db`; Docker sets `KYCC_DB_PATH=/data/kycc.db` via `docker-compose.yml`)

Env var names: `KYCC_NODE_TYPE`, `KYCC_NODE_HOST`, `KYCC_NODE_PORT`, `KYCC_NODE_USER`, `KYCC_NODE_PASSWORD`, `KYCC_NODE_NETWORK`, `KYCC_SERVER_HOST`, `KYCC_SERVER_PORT`, `KYCC_SERVER_DEBUG`, `KYCC_DB_PATH`.

### `kycc/adapters/` — Node adapters

Abstract base (`NodeAdapter`) defines two abstract methods that every adapter must implement:

```python
def get_raw_transaction(self, txid: str) -> dict
def get_block_height(self) -> int
```

`get_address_history(self, address: str) -> list[dict]` is a non-abstract default that raises `NotImplementedError`. Adapters that support it override it; the base implementation is a safe fallback.

**`BitcoinCoreAdapter`** (`bitcoincore.py`)

Uses `python-bitcoinrpc`'s `AuthServiceProxy`. Key design decision: a **fresh `AuthServiceProxy` is created on every RPC call** rather than reusing one instance. This avoids `CannotSendRequest` errors that occur when `http.client.HTTPConnection` (used internally by `AuthServiceProxy`) enters a stale/half-sent state after a failed or interrupted prior request.

```python
def _rpc(self) -> AuthServiceProxy:
    """Fresh proxy per call — avoids CannotSendRequest on stale connections."""
    return AuthServiceProxy(self._url)
```

`getrawtransaction` does not include `blockheight` in all Bitcoin Core versions — only `blockhash` is guaranteed for confirmed transactions. The adapter resolves the height via a second call to `getblockheader(blockhash)` and injects `blockheight` into the raw dict before it reaches the parser. For unconfirmed transactions (`blockhash` absent), `block_height` is `None`.

**`ElectrumAdapter`** (`electrum.py`)

Connects to an Electrum server via TCP JSON-RPC. Translates `blockchain.transaction.get` and `blockchain.scripthash.get_history` calls into the same `NodeAdapter` interface.

Electrum identifies addresses by scripthash — `SHA256(scriptPubKey_bytes)` with the bytes reversed. The adapter converts Bitcoin addresses to their scriptPubKey using `python-bitcoinlib` before making the scripthash query. The `network` parameter (passed from `Config.node_network`) is required so that testnet/regtest address prefixes are decoded correctly.

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

`FingerprintEngine` runs all enabled detectors over a `TxNode` and attaches `HeuristicResult` objects to `tx.annotations` via `annotate_inplace()`. Each `HeuristicResult` has:
- `code` — machine-readable identifier (e.g. `"UIOH"`, `"ADDRESS_REUSE"`)
- `severity` — `"info"` | `"warning"` | `"flag"`
- `description` — human-readable explanation
- `affected` — list of addresses or outpoints involved

See [HEURISTICS.md](HEURISTICS.md) for full detector documentation.

### `kycc/labels/` — BIP-329 label store

SQLite-backed. The schema is applied by `labels/migrator.py` on startup. Key tables:

```sql
CREATE TABLE labels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id   TEXT    NOT NULL DEFAULT 'default',
    ref_type    TEXT    NOT NULL CHECK(ref_type IN ('tx','utxo','addr','xpub')),
    ref         TEXT    NOT NULL,
    label       TEXT    NOT NULL,
    origin      TEXT    NOT NULL DEFAULT 'user',
    spendable   INTEGER,
    created_at  INTEGER NOT NULL,
    updated_at  INTEGER NOT NULL,
    UNIQUE(wallet_id, ref_type, ref)
);
```

Additional tables: `sessions` (graph session history), `heuristic_cache` (reserved for future use), `schema_meta` (migration version tracking).

Labels are wallet-namespaced so multiple wallets can label the same UTXO independently. `bip329.py` serialises rows to/from the JSONL format defined in BIP-329. The `wallet_id` field is internal and is not written to exported files.

### `kycc/routes/` — Flask API blueprints

Each route module is a separate `Blueprint` registered in `server.py`. See [FRONTEND.md](FRONTEND.md#api-client-apiclientts) for the full endpoint list.

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
- `loadedTxIds` — set of txids already in the graph; used to set the `canExpand` flag on UTXO input nodes
- `loadingTxIds` — set of txids currently being fetched; prevents duplicate in-flight requests
- `recentSessions` — loaded from `/api/sessions` on startup

Key actions:
- `loadRootTx(txid)` — fetches TX, builds nodes/edges, replaces the entire graph. Resets `loadedTxIds` to `{txid}` so expand buttons appear correctly on all inputs of the new root.
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

- The Electrum adapter cannot fetch a transaction by txid unless that transaction is indexed by the server (i.e. associated with a scripthash the server has seen). Full graph traversal of arbitrary on-chain transactions requires Bitcoin Core with `txindex=1`.
- Address history via Bitcoin Core (`scantxoutset`) only finds UTXOs in the current UTXO set — spent outputs are not returned. Use an Electrum server for full address history including spent outputs.
