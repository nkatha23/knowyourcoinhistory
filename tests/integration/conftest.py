"""
Integration test fixtures.

Requires a Bitcoin Core regtest node running on localhost:18443.
Start one with:

    docker compose -f docker-compose.regtest.yml up -d

The tests are skipped automatically if the node is not reachable,
so they are safe to run in CI without the sidecar (they just produce 0 tests).
"""

import pytest

from kycc.adapters.bitcoincore import BitcoinCoreAdapter

REGTEST_HOST = "127.0.0.1"
REGTEST_PORT = 18443
REGTEST_USER = "kycc"
REGTEST_PASS = "kyccpass"


def _node_available() -> bool:
    try:
        a = BitcoinCoreAdapter(REGTEST_HOST, REGTEST_PORT, REGTEST_USER, REGTEST_PASS)
        a.get_block_height()
        return True
    except Exception:
        return False


_NODE_UP = _node_available()

_SKIP_REASON = "Regtest Bitcoin Core node not available on localhost:18443"


@pytest.fixture(scope="session")
def adapter() -> BitcoinCoreAdapter:
    """A BitcoinCoreAdapter wired to the local regtest node.

    Skips all dependent tests if the node is not available.
    """
    if not _NODE_UP:
        pytest.skip(_SKIP_REASON)
    return BitcoinCoreAdapter(REGTEST_HOST, REGTEST_PORT, REGTEST_USER, REGTEST_PASS)


@pytest.fixture(scope="session")
def funded_address(adapter: BitcoinCoreAdapter) -> str:
    """
    Mines enough blocks so the coinbase is spendable (101 confirmations),
    then returns an address that has received funds.
    Idempotent — safe to call multiple times across the test session.
    """
    rpc = adapter._rpc  # direct access for setup; tests should use public API

    # Get or create a default wallet
    wallets = rpc.listwallets()
    if not wallets:
        try:
            rpc.createwallet("default")
        except Exception:
            pass  # wallet may already exist on disk

    address = rpc.getnewaddress()

    # Mine 101 blocks to make coinbase spendable
    rpc.generatetoaddress(101, address)

    return address


@pytest.fixture(scope="session")
def coinbase_txid(funded_address: str, adapter: BitcoinCoreAdapter) -> str:
    """Returns the txid of a real coinbase transaction from the regtest chain."""
    rpc = adapter._rpc
    best_hash = rpc.getbestblockhash()
    block = rpc.getblock(best_hash, 2)
    # The first transaction in any block is the coinbase
    return block["tx"][0]["txid"]


@pytest.fixture(scope="session")
def spend_txid(funded_address: str, adapter: BitcoinCoreAdapter) -> str:
    """
    Sends a small amount to a new address and returns the resulting txid.
    Mines one block so the tx is confirmed.
    """
    rpc = adapter._rpc
    recipient = rpc.getnewaddress()
    txid = rpc.sendtoaddress(recipient, 0.001)
    rpc.generatetoaddress(1, funded_address)
    return txid
