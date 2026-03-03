import json
from unittest.mock import MagicMock, patch
from kycc.adapters.electrum import ElectrumAdapter, _address_to_scripthash


def test_scripthash_is_64_hex_chars():
    h = _address_to_scripthash("bc1qtest")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_scripthash_different_addresses_differ():
    assert _address_to_scripthash("bc1qone") != _address_to_scripthash("bc1qtwo")


def _make_adapter(responses: list) -> ElectrumAdapter:
    encoded  = [(json.dumps({"id": i+1, "result": r}) + "\n").encode() for i, r in enumerate(responses)]
    mock_sock = MagicMock()
    mock_sock.recv    = MagicMock(side_effect=encoded)
    mock_sock.sendall = MagicMock()

    with patch("kycc.adapters.electrum.socket.create_connection", return_value=mock_sock), \
         patch("kycc.adapters.electrum.ssl.create_default_context") as mock_ssl:
        mock_ssl.return_value.wrap_socket.return_value = mock_sock
        adapter = ElectrumAdapter("localhost", 50002, use_ssl=True)

    adapter._sock = mock_sock
    return adapter


def test_get_block_height():
    adapter = _make_adapter([{"height": 850_000}])
    assert adapter.get_block_height() == 850_000


def test_get_address_history():
    history = [{"tx_hash": "a"*64, "height": 800_000}, {"tx_hash": "b"*64, "height": 800_001}]
    adapter = _make_adapter([history])
    result  = adapter.get_address_history("bc1qtest")
    assert len(result)           == 2
    assert result[0]["tx_hash"]  == "a" * 64


def test_get_address_history_empty():
    adapter = _make_adapter([[]])
    assert adapter.get_address_history("bc1qtest") == []
