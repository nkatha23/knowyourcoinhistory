"""
Integration tests for BitcoinCoreAdapter against a live regtest node.

These tests exercise the public adapter API end-to-end — real RPC calls,
real serialisation, real data shapes.  They are automatically skipped when
the regtest node is not available (see conftest.py).
"""

import pytest

from kycc.adapters.bitcoincore import BitcoinCoreAdapter
from kycc.graph.parser import parse_tx

# ── get_block_height ──────────────────────────────────────────────────────────


def test_get_block_height_returns_int(adapter: BitcoinCoreAdapter) -> None:
    height = adapter.get_block_height()
    assert isinstance(height, int)
    assert height >= 101  # conftest mines 101 blocks


# ── get_raw_transaction ───────────────────────────────────────────────────────


def test_get_raw_transaction_coinbase(
    adapter: BitcoinCoreAdapter, coinbase_txid: str
) -> None:
    raw = adapter.get_raw_transaction(coinbase_txid)
    assert isinstance(raw, dict)
    assert raw["txid"] == coinbase_txid
    assert "vin" in raw
    assert "vout" in raw
    # Coinbase tx has no prevout in vin
    assert "coinbase" in raw["vin"][0]


def test_get_raw_transaction_spend(
    adapter: BitcoinCoreAdapter, spend_txid: str
) -> None:
    raw = adapter.get_raw_transaction(spend_txid)
    assert isinstance(raw, dict)
    assert raw["txid"] == spend_txid
    # Non-coinbase inputs should have prevout resolved
    vin = raw["vin"][0]
    assert "txid" in vin
    assert "vout" in vin


def test_get_raw_transaction_unknown_raises(adapter: BitcoinCoreAdapter) -> None:
    fake_txid = "a" * 64
    with pytest.raises(Exception):
        adapter.get_raw_transaction(fake_txid)


# ── TxParser round-trip ───────────────────────────────────────────────────────


def test_parser_parses_coinbase(
    adapter: BitcoinCoreAdapter, coinbase_txid: str
) -> None:
    raw = adapter.get_raw_transaction(coinbase_txid)
    tx = parse_tx(raw)
    assert tx.txid == coinbase_txid
    assert tx.is_coinbase is True
    assert len(tx.inputs) == 1
    assert len(tx.outputs) >= 1
    assert tx.fee_sats is None  # coinbase has no fee


def test_parser_parses_spend(adapter: BitcoinCoreAdapter, spend_txid: str) -> None:
    raw = adapter.get_raw_transaction(spend_txid)
    tx = parse_tx(raw)
    assert tx.txid == spend_txid
    assert tx.is_coinbase is False
    assert len(tx.inputs) >= 1
    assert len(tx.outputs) >= 1
    # fee should be calculable (all inputs have prevout value)
    assert tx.fee_sats is not None
    assert tx.fee_sats >= 0


def test_parser_output_values_positive(
    adapter: BitcoinCoreAdapter, spend_txid: str
) -> None:
    raw = adapter.get_raw_transaction(spend_txid)
    tx = parse_tx(raw)
    for out in tx.outputs:
        assert out.value_sats > 0, f"output {out.vout} has non-positive value"


# ── get_address_history ───────────────────────────────────────────────────────


def test_get_address_history_funded(
    adapter: BitcoinCoreAdapter, funded_address: str
) -> None:
    history = adapter.get_address_history(funded_address)
    assert isinstance(history, list)
    # The funded address received coinbase rewards, so it must have UTXOs
    assert len(history) > 0
    for entry in history:
        assert "tx_hash" in entry
        assert len(entry["tx_hash"]) == 64  # valid txid


def test_get_address_history_unknown_address(adapter: BitcoinCoreAdapter) -> None:
    # A fresh address that has never been used should return an empty list
    new_addr = adapter._rpc.getnewaddress()
    history = adapter.get_address_history(new_addr)
    assert history == []


# ── FingerprintEngine end-to-end ──────────────────────────────────────────────


def test_fingerprint_engine_on_regtest_tx(
    adapter: BitcoinCoreAdapter, spend_txid: str
) -> None:
    from kycc.fingerprint.engine import FingerprintEngine
    from kycc.graph.parser import parse_tx

    raw = adapter.get_raw_transaction(spend_txid)
    tx = parse_tx(raw)

    engine = FingerprintEngine()
    annotations = engine.annotate(tx)

    # Annotations should be a list (possibly empty for clean regtest txs)
    assert isinstance(annotations, list)
    for a in annotations:
        assert hasattr(a, "code")
        assert hasattr(a, "severity")
        assert hasattr(a, "description")
