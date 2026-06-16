from unittest.mock import MagicMock, patch

from kycc.adapters.bitcoincore import BitcoinCoreAdapter


def test_get_raw_transaction_confirmed_adds_block_height():
    tx = {"txid": "a" * 64, "blockhash": "b" * 64}
    rpc = MagicMock()
    rpc.getrawtransaction.return_value = tx.copy()
    rpc.getblockheader.return_value = {"height": 850_000}

    with patch("kycc.adapters.bitcoincore.AuthServiceProxy", return_value=rpc):
        adapter = BitcoinCoreAdapter("127.0.0.1", 8332, "user", "pass")
        result = adapter.get_raw_transaction("a" * 64)

    rpc.getrawtransaction.assert_called_once_with("a" * 64, 2)
    rpc.getblockheader.assert_called_once_with("b" * 64)
    assert result["blockheight"] == 850_000


def test_get_raw_transaction_unconfirmed_keeps_result_without_block_height():
    tx = {"txid": "a" * 64}
    rpc = MagicMock()
    rpc.getrawtransaction.return_value = tx.copy()

    with patch("kycc.adapters.bitcoincore.AuthServiceProxy", return_value=rpc):
        adapter = BitcoinCoreAdapter("127.0.0.1", 8332, "user", "pass")
        result = adapter.get_raw_transaction("a" * 64)

    rpc.getrawtransaction.assert_called_once_with("a" * 64, 2)
    rpc.getblockheader.assert_not_called()
    assert "blockheight" not in result


def test_get_block_height():
    rpc = MagicMock()
    rpc.getblockcount.return_value = 850_123

    with patch("kycc.adapters.bitcoincore.AuthServiceProxy", return_value=rpc):
        adapter = BitcoinCoreAdapter("127.0.0.1", 8332, "user", "pass")
        assert adapter.get_block_height() == 850_123

    rpc.getblockcount.assert_called_once_with()


def test_get_address_history_maps_scan_unspents():
    rpc = MagicMock()
    rpc.scantxoutset.return_value = {
        "unspents": [
            {"txid": "a" * 64, "height": 850_000},
            {"txid": "b" * 64},
        ]
    }

    with patch("kycc.adapters.bitcoincore.AuthServiceProxy", return_value=rpc):
        adapter = BitcoinCoreAdapter("127.0.0.1", 8332, "user", "pass")
        result = adapter.get_address_history("bc1qexample")

    rpc.scantxoutset.assert_called_once_with("start", ["addr(bc1qexample)"])
    assert result == [
        {"tx_hash": "a" * 64, "height": 850_000},
        {"tx_hash": "b" * 64, "height": 0},
    ]
