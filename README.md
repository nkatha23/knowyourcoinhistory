# Know Your Coin History (KYCC)

> A privacy-preserving Bitcoin transaction graph explorer for labeling and auditing your own coin history.

Proposed by [0xB10C](https://github.com/0xB10C/project-ideas/issues/13). KYCC lets you load a transaction or UTXO, recursively trace its ancestry, attach labels, detect wallet fingerprinting heuristics, and export everything in the [BIP-329](https://github.com/bitcoin/bips/blob/master/bip-0329.mediawiki) wallet label standard — all against your own local Bitcoin Core node or Electrum server. No third-party APIs. No telemetry.

---

## What It Does

- **Transaction graph traversal** — enter a txid, outpoint, or address and walk backwards through ancestor transactions interactively
- **UTXO and transaction labeling** — attach labels to any node in the graph, persisted locally in SQLite
- **BIP-329 import/export** — exchange labels with Sparrow Wallet, Electrum 4.x, and Bitcoin Core 27+ descriptor wallets
- **Wallet fingerprinting heuristics** — detect UIOH, address reuse, round payments, change output inference, script type mismatch, RBF signaling, locktime patterns, and consolidation behavior
- **Multi-wallet sessions** — merge UTXO sets and label namespaces from multiple wallets in a single graph view
- **Privacy-first** — binds to localhost only, supports Tor SOCKS5 proxy, zero external network calls

---

## Architecture
```
Browser (React + ReactFlow)
        │  HTTP/JSON (localhost)
Flask API Server (Python 3.11+)
        │
   NodeAdapter ABC
   ┌────┴────┐
Bitcoin Core  Electrum Server
  JSON-RPC    TCP/SSL
```

Full architecture and engineering spec: [`docs/`](./docs/)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask 3.x, SQLite3 |
| Node connectivity | python-bitcoinrpc, python-bitcoinlib |
| Frontend | React 19, TypeScript, Vite 7 |
| Graph UI | @xyflow/react v12 (React Flow) |
| State | Zustand |
| Styling | Tailwind CSS v4, framer-motion, Sonner |
| Testing | pytest, pytest-cov |
| Linting | black, ruff, mypy |

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- A synced Bitcoin Core node **or** an Electrum server (Fulcrum / electrs)
- Regtest mode supported for local development (see [docs/REGTEST_SETUP.md](./docs/REGTEST_SETUP.md))

---

## Quickstart

### 1. Clone and enter the repo
```bash
git clone https://github.com/nkatha23/knowyourcoinhistory.git
cd knowyourcoinhistory
```

### 2. Set up Python environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask python-bitcoinrpc python-bitcoinlib pytest pytest-cov black ruff mypy
```

### 3. Configure your node connection
```bash
cp kycc.toml.example kycc.toml
```

Edit `kycc.toml`:
```toml
[node]
type        = "bitcoincore"
host        = "127.0.0.1"
port        = 8332
cookie_file = "/home/YOU/.bitcoin/.cookie"
network     = "mainnet"
```

### 4. Start the backend
```bash
make dev-backend
# or: source .venv/bin/activate && python main.py
# API running at http://127.0.0.1:5050
```

### 5. Start the frontend
```bash
make dev-frontend
# or: cd web && npm run dev
# UI running at http://localhost:5173
```

### 6. Verify
```bash
curl http://127.0.0.1:5050/api/health
# {"ok": true, "version": "0.1.0"}
```

---

## Running Tests

**Unit tests** (no node required):
```bash
pytest tests/unit/ -v --cov=kycc
```

**Integration tests** (requires regtest node — see [docs/REGTEST_SETUP.md](./docs/REGTEST_SETUP.md)):
```bash
docker compose -f docker-compose.regtest.yml up -d
pytest tests/integration/ -v
```

**All tests:**
```bash
pytest tests/ -v --cov=kycc
```

---

## BIP-329 Label Format

KYCC imports and exports labels in the BIP-329 JSON Lines format:
```jsonl
{ "type": "tx",   "ref": "a1b2c3...",    "label": "Exchange withdrawal" }
{ "type": "utxo", "ref": "a1b2c3...:0",  "label": "KYC tainted" }
{ "type": "addr", "ref": "bc1q...",       "label": "Cold storage" }
```

Compatible with Sparrow Wallet, Electrum 4.x, and Bitcoin Core 27+.

---

## Project Structure
```
kycc/                    Python package
  adapters/              NodeAdapter ABC + Bitcoin Core / Electrum implementations
  graph/                 Transaction graph resolver, parser, dataclasses
  labels/                SQLite label store + BIP-329 serializer
  fingerprint/           Wallet heuristic detection engine
  routes/                Flask API blueprints
tests/                   pytest unit + integration tests
web/                     React SPA (Vite 7 + TypeScript)
  src/
    components/
      Graph/
        GraphCanvas.tsx        React Flow container
        EmptyState.tsx         Hero landing page with search + info cards
        FloatingSearch.tsx     Compact pill search overlay (shown when graph loaded)
        TransactionNode.tsx    TX graph node (280px, orange top border)
        UTXONode.tsx           UTXO pill node (200px, green/gold borders)
      Toolbar.tsx              Logo, wallet selector, fingerprint toggle, import/export
      RightPanel.tsx           Label editor + fingerprint annotation panel
      SettingsModal.tsx        Node status + heuristic toggles
    api/                 Typed fetch wrappers for all /api/* routes
    store/               Zustand graph + session state + edge layout
    types/               Shared TypeScript interfaces
docs/                    Architecture, heuristics, setup guides
docker-compose.regtest.yml  Bitcoin Core v28 regtest node
.github/workflows/ci.yml    ruff + black + pytest (Python 3.11 & 3.12)
```

---

## Wallet Fingerprinting Heuristics

| Heuristic | Description |
|---|---|
| UIOH | Unnecessary input ownership heuristic — detects redundant inputs |
| Address Reuse | Input address appears in outputs or prior labeled transactions |
| Round Payment | Output value divisible by common round-number thresholds |
| Change Inference | Probable change output detected by script type match + value |
| Script Mismatch | Heterogeneous input/output script types |
| RBF Signaling | nSequence ≤ 0xFFFFFFFD on any input |
| Locktime Pattern | Classifies locktime as none / block_height / unix_timestamp |
| Consolidation | 3+ inputs, 1–2 outputs — likely a UTXO management transaction |

---

## Roadmap

- [x] Repo structure and Flask skeleton
- [x] Phase 0 — Bitcoin Core RPC adapter + TxParser
- [x] Phase 1 — Label store + BIP-329 import/export
- [x] Phase 2 — Fingerprinting heuristic engine (8 detectors, 89 tests)
- [x] Phase 3 — Flask API routes + serializer
- [x] Phase 4 — Electrum adapter + multi-wallet sessions
- [x] Phase 5 — React + React Flow interactive graph UI
- [x] Phase 5+ — Frontend redesign: hero landing page, floating search, node typography, edge value labels
- [x] Bug fixes — BitcoinCoreAdapter stale connection (`CannotSendRequest`), `decimal.Decimal` × float TypeError in parser
- [ ] Phase 6 — Signet public demo

---

## Contributing

This project is in active early development. If you are working on a related Bitcoin labeling or privacy tool, feel free to open an issue. Discussion happens on the [original project proposal](https://github.com/0xB10C/project-ideas/issues/13).

---

## License

MIT

---

## Acknowledgements

- [0xB10C](https://github.com/0xB10C) for the original project idea and specification
- [Coin Smith](https://github.com/nkatha23/coin-smith) — PSBT/UTXO logic this project descends from
