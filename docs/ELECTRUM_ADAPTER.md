# Electrum Adapter

KYCC supports Electrum servers (Fulcrum, electrs, ElectrumX) as an alternative to Bitcoin Core. The Electrum adapter implements the same `NodeAdapter` interface as the Bitcoin Core adapter.

---

## Configuration

Edit `kycc.toml`:

```toml
[node]
type    = "electrum"
host    = "127.0.0.1"
port    = 50001          # TCP plaintext; use 50002 for SSL
network = "mainnet"      # mainnet | testnet | signet
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
| Fetch raw transaction by txid | Yes (`txindex=1`) | Yes |
| Address history | `scantxoutset` (UTXO set only) | Full history via scripthash |
| Block height | `getblockcount` | `blockchain.headers.subscribe` |
| Graph expansion (parent TXs) | Yes | Yes (for indexed transactions) |

---

## Limitations

- Electrum servers index transactions by address/scripthash. Fetching an arbitrary txid that is not associated with any of your addresses may fail on some server implementations.
- `get_address_history` returns confirmed and mempool transactions for the address, unlike Bitcoin Core's `scantxoutset` which only returns current UTXO set members.
- For full graph traversal of arbitrary on-chain transactions, Bitcoin Core with `txindex=1` is recommended.

---

## Running a Local Electrum Server

For regtest development, you can run Fulcrum against a local Bitcoin Core node:

```bash
# Install Fulcrum (https://github.com/cculianu/Fulcrum)
# Configure Fulcrum to connect to your regtest bitcoind
# Then set kycc.toml to type = "electrum", port = 50001
```

For mainnet, connect to a trusted server or your own instance.
