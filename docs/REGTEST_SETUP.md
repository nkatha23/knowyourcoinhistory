# Local Regtest Setup

This guide walks you through spinning up a local Bitcoin Core **regtest** node so you can test and develop KYCC without touching mainnet or signet funds.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Docker + Docker Compose | Docker ≥ 24.0 |
| Python | 3.11+ |
| Node.js | 20+ |

---

## 1. Start the Regtest Node

A pre-configured `docker-compose.regtest.yml` is included at the repo root.

```bash
docker compose -f docker-compose.regtest.yml up -d
```

This starts Bitcoin Core v28 in regtest mode with:

- RPC on `localhost:18443`
- Credentials: `kycc` / `kyccpass`
- `txindex=1` so arbitrary transactions can be fetched by txid

Confirm it is healthy:

```bash
docker compose -f docker-compose.regtest.yml ps
# bitcoind   running (healthy)
```

---

## 2. Configure KYCC

Copy the example config and point it at the regtest node:

```bash
cp kycc.toml.example kycc.toml
```

Edit `kycc.toml`:

```toml
[node]
type     = "bitcoincore"
host     = "127.0.0.1"
port     = 18443
user     = "kycc"
password = "kyccpass"
network  = "regtest"

[server]
host  = "127.0.0.1"
port  = 5050
debug = true

[db]
path = "kycc.db"
```

---

## 3. Mine Some Blocks

Regtest starts with no blocks and no spendable coins. Use the helper commands below to create a funded wallet and mine blocks.

```bash
# Open a shell inside the container
docker compose -f docker-compose.regtest.yml exec bitcoind bash

# Inside the container — create a wallet and mine 101 blocks
bitcoin-cli -regtest -rpcuser=kycc -rpcpassword=kyccpass createwallet "default"
ADDR=$(bitcoin-cli -regtest -rpcuser=kycc -rpcpassword=kyccpass getnewaddress)
bitcoin-cli -regtest -rpcuser=kycc -rpcpassword=kyccpass generatetoaddress 101 $ADDR

# Check balance (should be 50 BTC from the first coinbase, now spendable)
bitcoin-cli -regtest -rpcuser=kycc -rpcpassword=kyccpass getbalance
```

---

## 4. Create a Test Transaction

Send coins to a new address so you have a non-coinbase transaction to explore:

```bash
# Still inside the container
RECIPIENT=$(bitcoin-cli -regtest -rpcuser=kycc -rpcpassword=kyccpass getnewaddress)
TXID=$(bitcoin-cli -regtest -rpcuser=kycc -rpcpassword=kyccpass sendtoaddress $RECIPIENT 1.5)
bitcoin-cli -regtest -rpcuser=kycc -rpcpassword=kyccpass generatetoaddress 1 $ADDR

echo "Your test txid: $TXID"
```

Exit the container shell and paste the txid into the KYCC search bar.

---

## 5. Start the KYCC Backend

```bash
# From the repo root, with your venv active
python -m kycc.server
# Listening on http://127.0.0.1:5050
```

Test the connection:

```bash
curl http://127.0.0.1:5050/api/health
# {"ok": true, "node_online": true, "network": "regtest", ...}
```

---

## 6. Start the Frontend

```bash
cd web && npm run dev
# http://localhost:5173
```

Open the app, click **Settings → Re-check** to confirm the node is detected, then paste your `$TXID` into the search bar.

---

## 7. Run Integration Tests

The integration tests in `tests/integration/` connect directly to the regtest node. They are skipped automatically when the node is not running.

```bash
# Make sure the regtest container is up, then:
pytest tests/integration/ -v
```

Expected output with the node running:

```
tests/integration/test_rpc_adapter.py::test_get_block_height_returns_int PASSED
tests/integration/test_rpc_adapter.py::test_get_raw_transaction_coinbase PASSED
tests/integration/test_rpc_adapter.py::test_get_raw_transaction_spend PASSED
tests/integration/test_rpc_adapter.py::test_get_raw_transaction_unknown_raises PASSED
tests/integration/test_rpc_adapter.py::test_parser_parses_coinbase PASSED
tests/integration/test_rpc_adapter.py::test_parser_parses_spend PASSED
tests/integration/test_rpc_adapter.py::test_parser_output_values_positive PASSED
tests/integration/test_rpc_adapter.py::test_get_address_history_funded PASSED
tests/integration/test_rpc_adapter.py::test_get_address_history_unknown_address PASSED
tests/integration/test_rpc_adapter.py::test_fingerprint_engine_on_regtest_tx PASSED
```

Without the node running all integration tests are skipped (not failed).

---

## 8. Tear Down

```bash
docker compose -f docker-compose.regtest.yml down -v
```

The `-v` flag removes the data volume so the chain is fully reset next time.

---

## Troubleshooting

### "Connection refused" on port 18443

The container may still be starting. Wait for it to become healthy:

```bash
docker compose -f docker-compose.regtest.yml ps
```

If it never becomes healthy, check the logs:

```bash
docker compose -f docker-compose.regtest.yml logs bitcoind
```

### "Insufficient funds" errors

Regtest coinbase outputs require 100 confirmations before they are spendable. Mine at least 101 blocks with `generatetoaddress`.

### "Transaction not found" in KYCC

Ensure `txindex=1` is in the node config. The Docker Compose file sets this by default. If you are using your own Bitcoin Core instance, add `txindex=1` to `bitcoin.conf` and reindex:

```bash
bitcoind -reindex
```

### Backend shows node offline after mining

Click **Settings → Re-check** or restart the backend. The health check runs once on startup.
