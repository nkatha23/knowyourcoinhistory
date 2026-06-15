"""
Route tests use a mock adapter so no real Bitcoin node is needed.
"""

import json
import tempfile
from unittest.mock import MagicMock

import pytest
from flask import Flask

from kycc.fingerprint.engine import FingerprintEngine
from kycc.labels.store import LabelStore
from kycc.routes.export import bp as export_bp
from kycc.routes.health import bp as health_bp
from kycc.routes.labels import bp as labels_bp
from kycc.routes.session import bp as session_bp
from kycc.routes.tx import bp as tx_bp

MOCK_TXID = "a" * 64
MOCK_RAW_TX = {
    "txid": MOCK_TXID,
    "version": 2,
    "locktime": 0,
    "size": 141,
    "weight": 564,
    "vin": [
        {
            "txid": "b" * 64,
            "vout": 0,
            "sequence": 0xFFFFFFFF,
            "prevout": {
                "value": 0.001,
                "scriptPubKey": {
                    "hex": "0014" + "a" * 40,
                    "address": "bc1qinput",
                },
            },
        }
    ],
    "vout": [
        {
            "n": 0,
            "value": 0.0009,
            "scriptPubKey": {
                "hex": "0014" + "b" * 40,
                "address": "bc1qoutput",
            },
        }
    ],
}


def _make_test_app(network: str = "regtest"):
    from dataclasses import dataclass

    @dataclass
    class _FakeCfg:
        node_type: str = "bitcoincore"
        node_host: str = "127.0.0.1"
        node_port: int = 8332
        node_network: str = network

    app = Flask(__name__)
    app.config["TESTING"] = True

    mock_adapter = MagicMock()
    mock_adapter.get_raw_transaction.return_value = MOCK_RAW_TX
    mock_adapter.get_block_height.return_value = 100

    app.config["NODE_ADAPTER"] = mock_adapter
    app.config["LABEL_STORE"] = LabelStore(tempfile.mktemp(suffix=".db"))
    app.config["FINGERPRINT_ENGINE"] = FingerprintEngine()
    app.config["KYCC_CONFIG"] = _FakeCfg()
    app.config["ENABLED_HEURISTICS"] = []

    from kycc.routes.address import bp as address_bp

    for bp in [health_bp, tx_bp, labels_bp, export_bp, session_bp, address_bp]:
        app.register_blueprint(bp)
    return app


@pytest.fixture
def client():
    app = _make_test_app()
    with app.test_client() as c:
        yield c


# ── health ────────────────────────────────────────────────────────────────────


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


# ── GET /api/tx ───────────────────────────────────────────────────────────────


def test_get_tx_returns_txnode(client):
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    data = res.get_json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["tx"]["txid"] == MOCK_TXID


def test_get_tx_has_inputs_outputs(client):
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    tx = res.get_json()["tx"]
    assert len(tx["inputs"]) == 1
    assert len(tx["outputs"]) == 1


def test_get_tx_fee_correct(client):
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    tx = res.get_json()["tx"]
    assert tx["fee_sats"] == 10_000


def test_get_tx_has_annotations(client):
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    tx = res.get_json()["tx"]
    assert "annotations" in tx
    assert isinstance(tx["annotations"], list)


def test_get_tx_missing_txid(client):
    res = client.get("/api/tx")
    assert res.status_code == 400


def test_get_tx_invalid_txid_length(client):
    res = client.get("/api/tx?txid=abc123")
    assert res.status_code == 400


# ── POST /api/label ───────────────────────────────────────────────────────────


def test_post_label(client):
    res = client.post(
        "/api/label",
        json={"ref_type": "tx", "ref": "a" * 64, "label": "Test label"},
    )
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_post_label_invalid_ref_type(client):
    res = client.post(
        "/api/label",
        json={"ref_type": "invoice", "ref": "abc", "label": "bad"},
    )
    assert res.status_code == 400


def test_post_label_empty_label(client):
    res = client.post(
        "/api/label",
        json={"ref_type": "tx", "ref": "a" * 64, "label": ""},
    )
    assert res.status_code == 400


# ── GET /api/labels ───────────────────────────────────────────────────────────


def test_list_labels_empty(client):
    res = client.get("/api/labels")
    data = res.get_json()
    assert res.status_code == 200
    assert data["labels"] == []
    assert data["count"] == 0


def test_list_labels_after_insert(client):
    client.post(
        "/api/label",
        json={"ref_type": "tx", "ref": "a" * 64, "label": "inserted"},
    )
    res = client.get("/api/labels")
    data = res.get_json()
    assert data["count"] == 1
    assert data["labels"][0]["label"] == "inserted"


# ── DELETE /api/label ─────────────────────────────────────────────────────────


def test_delete_label(client):
    client.post(
        "/api/label",
        json={"ref_type": "tx", "ref": "a" * 64, "label": "to delete"},
    )
    res = client.delete("/api/label", json={"ref_type": "tx", "ref": "a" * 64})
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


# ── GET /api/labels/export ────────────────────────────────────────────────────


def test_export_empty(client):
    res = client.get("/api/labels/export")
    assert res.status_code == 200
    assert res.data == b""


def test_export_after_insert(client):
    client.post(
        "/api/label",
        json={"ref_type": "tx", "ref": "a" * 64, "label": "exported"},
    )
    res = client.get("/api/labels/export")
    line = json.loads(res.data.decode())
    assert line["label"] == "exported"
    assert line["type"] == "tx"


# ── POST /api/labels/import ───────────────────────────────────────────────────


def test_import_labels(client):
    jsonl = '{"type":"tx","ref":"' + "a" * 64 + '","label":"imported"}'
    res = client.post(
        "/api/labels/import",
        data=jsonl,
        content_type="application/x-ndjson",
    )
    assert res.status_code == 200
    assert res.get_json()["imported"] == 1


def test_import_then_tx_has_label(client):
    jsonl = '{"type":"tx","ref":"' + MOCK_TXID + '","label":"from sparrow"}'
    client.post(
        "/api/labels/import",
        data=jsonl,
        content_type="application/x-ndjson",
    )
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    tx = res.get_json()["tx"]
    assert tx["label"] == "from sparrow"


#  address search route test coverage
#  regtest prefix & placeholder 
MOCK_ADDRESS = "bcrt1q" + "a" * 39   
# mainnet prefix& placeholder 
MAINNET_ADDRESS = "bc1q" + "a" * 39

def test_get_address_valid_returns_history(client):
    adapter = client.application.config["NODE_ADAPTER"]
    adapter.get_address_history.return_value = [
        {"tx_hash": "a" * 64, "height": 800_000},
        {"tx_hash": "b" * 64, "height": 800_001},
    ]
    res = client.get(f"/api/address?address={MOCK_ADDRESS}")
    data = res.get_json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["address"] == MOCK_ADDRESS
    assert data["count"] == 2
    assert data["history"][0]["tx_hash"] == "a" * 64


def test_get_address_unknown_returns_empty_list(client):
    adapter = client.application.config["NODE_ADAPTER"]
    adapter.get_address_history.return_value = []
    res = client.get(f"/api/address?address={MOCK_ADDRESS}")
    data = res.get_json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["count"] == 0
    assert data["history"] == []


def test_get_address_missing_param_returns_400(client):
    res = client.get("/api/address")
    data = res.get_json()
    assert res.status_code == 400
    assert data["ok"] is False


def test_get_address_adapter_error_returns_502(client):
    adapter = client.application.config["NODE_ADAPTER"]
    adapter.get_address_history.side_effect = RuntimeError("node unreachable")
    res = client.get(f"/api/address?address={MOCK_ADDRESS}")
    data = res.get_json()
    assert res.status_code == 502
    assert data["ok"] is False


def test_get_address_wrong_network_returns_400(client):
    # app is configured for regtest; a bc1q (mainnet) address must be rejected
    res = client.get(f"/api/address?address={MAINNET_ADDRESS}")
    data = res.get_json()
    assert res.status_code == 400
    assert data["ok"] is False


TESTNET_ADDRESS = "tb1q" + "a" * 39  # testnet/signet prefix, placeholder data


def test_get_address_testnet_address_accepted_on_testnet():
    app = _make_test_app(network="testnet")
    app.config["NODE_ADAPTER"].get_address_history.return_value = []
    with app.test_client() as c:
        res = c.get(f"/api/address?address={TESTNET_ADDRESS}")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_get_address_signet_address_accepted_on_signet():
    # signet shares the tb1 HRP with testnet
    app = _make_test_app(network="signet")
    app.config["NODE_ADAPTER"].get_address_history.return_value = []
    with app.test_client() as c:
        res = c.get(f"/api/address?address={TESTNET_ADDRESS}")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_get_address_testnet_address_rejected_on_regtest(client):
    res = client.get(f"/api/address?address={TESTNET_ADDRESS}")
    data = res.get_json()
    assert res.status_code == 400
    assert data["ok"] is False


def test_get_address_testnet_address_rejected_on_mainnet():
    app = _make_test_app(network="mainnet")
    with app.test_client() as c:
        res = c.get(f"/api/address?address={TESTNET_ADDRESS}")
    data = res.get_json()
    assert res.status_code == 400
    assert data["ok"] is False


# ── _address_to_scripthash (ElectrumAdapter) ─────────────────────────────────
# BIP-173 canonical mainnet P2WPKH test vector — checksummed, known-good.
_BIP173_MAINNET = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"


def test_address_to_scripthash_wrong_network_raises():
    from kycc.adapters.electrum import _address_to_scripthash

    with pytest.raises(Exception):
        _address_to_scripthash(_BIP173_MAINNET, "regtest")


def test_address_to_scripthash_mainnet_returns_hex():
    from kycc.adapters.electrum import _address_to_scripthash

    result = _address_to_scripthash(_BIP173_MAINNET, "mainnet")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)
