# Electrum Adapter

KYCC supports Electrum servers (Fulcrum, electrs, ElectrumX) as an alternative to Bitcoin Core. The Electrum adapter implements the same `NodeAdapter` interface as the Bitcoin Core adapter.

---

## Configuration

**Option A — `kycc.toml`:**

```toml
[node]
type    = "electrum"
host    = "127.0.0.1"
port    = 50001          # TCP plaintext; use 50002 for SSL
network = "mainnet"      # mainnet | testnet | signet | regtest
```

**Option B — env vars (Docker or no-file preference):**

```bash
export KYCC_NODE_TYPE=electrum
export KYCC_NODE_HOST=127.0.0.1
export KYCC_NODE_PORT=50001
export KYCC_NODE_NETWORK=mainnet
```

No `user` or `password` fields are needed for Electrum (most public/local servers are unauthenticated).

---

## Supported Servers

| Software | Default Port (TCP) | Default Port (SSL) |
|----------|-------------------|-------------------|
| Fulcrum  | 50001 | 50002 |
| electrs  | 50001 | 50002 |
| ElectrumX | 50001 | 50002 |

---

## Capabilities

| Feature | Bitcoin Core | Electrum |
|---------|-------------|----------|
| Fetch raw transaction by txid | Yes (`txindex=1` recommended) | Yes (for indexed transactions) |
| Address history — spent outputs | No (`scantxoutset` returns UTXO set only) | Yes (full history via scripthash) |
| Address history — unconfirmed | No | Yes (mempool included) |
| Block height | `getblockcount` | `blockchain.headers.subscribe` |
| Graph expansion (parent TXs) | Yes | Yes (for indexed transactions) |

---

## Scripthash calculation

Electrum identifies addresses by scripthash: `SHA256(scriptPubKey_bytes)` with the result byte-reversed. The adapter converts a Bitcoin address to its scriptPubKey using `python-bitcoinlib` before querying the server. The `network` setting in `kycc.toml` (or `KYCC_NODE_NETWORK` env var) must be set correctly so that testnet and regtest address prefixes decode without error.

---

## Limitations

- Electrum servers index transactions by scripthash. Fetching an arbitrary txid not associated with any indexed address may fail depending on the server implementation. For full graph traversal of arbitrary on-chain transactions, Bitcoin Core with `txindex=1` is recommended.
- `get_address_history` returns confirmed and unconfirmed (mempool) transactions, unlike Bitcoin Core's `scantxoutset` which returns only the current UTXO set.

---

## Running a Local Electrum Server

For regtest development, you can run Fulcrum against a local Bitcoin Core node:

```bash
# Install Fulcrum (https://github.com/cculianu/Fulcrum)
# Configure Fulcrum to connect to your regtest bitcoind
# Then set kycc.toml to type = "electrum", port = 50001
```

For mainnet, connect to a trusted server or your own instance.
