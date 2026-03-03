"""
Route tests use a mock adapter so no real Bitcoin node is needed.
"""
import json
import pytest
from unittest.mock import MagicMock
from kycc.server import create_app
from kycc.labels.store import LabelStore
from kycc.fingerprint.engine import FingerprintEngine
import tempfile


# ── minimal raw tx the mock adapter returns ───────────────────────────────────
MOCK_TXID = "a" * 64
MOCK_RAW_TX = {
    "txid": MOCK_TXID,
    "version": 2, "locktime": 0, "size": 141, "weight": 564,
    "vin": [{
        "txid": "b" * 64, "vout": 0, "sequence": 0xFFFFFFFF,
        "prevout": {
            "value": 0.001,
            "scriptPubKey": {"hex": "0014" + "a" * 40, "address": "bc1qinput"},
        },
    }],
    "vout": [{
        "n": 0, "value": 0.0009,
        "scriptPubKey": {"hex": "0014" + "b" * 40, "address": "bc1qoutput"},
    }],
}


@pytest.fixture
def client():
    app = create_app.__wrapped__() if hasattr(create_app, "__wrapped__") \
        else _make_test_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _make_test_app():
    from flask import Flask
    from kycc.routes.health import bp as health_bp
    from kycc.routes.tx     import bp as tx_bp
    from kycc.routes.labels import bp as labels_bp
    from kycc.routes.export import bp as export_bp

    app = Flask(__name__)
    app.config["TESTING"] = True

    mock_adapter = MagicMock()
    mock_adapter.get_raw_transaction.return_value = MOCK_RAW_TX

    app.config["NODE_ADAPTER"]       = mock_adapter
    app.config["LABEL_STORE"]        = LabelStore(tempfile.mktemp(suffix=".db"))
    app.config["FINGERPRINT_ENGINE"] = FingerprintEngine()

    app.register_blueprint(health_bp)
    app.register_blueprint(tx_bp)
    app.register_blueprint(labels_bp)
    app.register_blueprint(export_bp)
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
    res  = client.get(f"/api/tx?txid={MOCK_TXID}")
    data = res.get_json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["tx"]["txid"] == MOCK_TXID


def test_get_tx_has_inputs_outputs(client):
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    tx  = res.get_json()["tx"]
    assert len(tx["inputs"])  == 1
    assert len(tx["outputs"]) == 1


def test_get_tx_fee_correct(client):
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    tx  = res.get_json()["tx"]
    assert tx["fee_sats"] == 10_000


def test_get_tx_has_annotations(client):
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    tx  = res.get_json()["tx"]
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
    res = client.post("/api/label", json={
        "ref_type": "tx", "ref": "a" * 64, "label": "Test label"
    })
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_post_label_invalid_ref_type(client):
    res = client.post("/api/label", json={
        "ref_type": "invoice", "ref": "abc", "label": "bad"
    })
    assert res.status_code == 400


def test_post_label_empty_label(client):
    res = client.post("/api/label", json={
        "ref_type": "tx", "ref": "a" * 64, "label": ""
    })
    assert res.status_code == 400


# ── GET /api/labels ───────────────────────────────────────────────────────────

def test_list_labels_empty(client):
    res  = client.get("/api/labels")
    data = res.get_json()
    assert res.status_code == 200
    assert data["labels"] == []
    assert data["count"]  == 0


def test_list_labels_after_insert(client):
    client.post("/api/label", json={
        "ref_type": "tx", "ref": "a" * 64, "label": "inserted"
    })
    res  = client.get("/api/labels")
    data = res.get_json()
    assert data["count"] == 1
    assert data["labels"][0]["label"] == "inserted"


# ── DELETE /api/label ─────────────────────────────────────────────────────────

def test_delete_label(client):
    client.post("/api/label", json={
        "ref_type": "tx", "ref": "a" * 64, "label": "to delete"
    })
    res = client.delete("/api/label", json={
        "ref_type": "tx", "ref": "a" * 64
    })
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


# ── GET /api/labels/export ────────────────────────────────────────────────────

def test_export_empty(client):
    res = client.get("/api/labels/export")
    assert res.status_code == 200
    assert res.data == b""


def test_export_after_insert(client):
    client.post("/api/label", json={
        "ref_type": "tx", "ref": "a" * 64, "label": "exported"
    })
    res  = client.get("/api/labels/export")
    line = json.loads(res.data.decode())
    assert line["label"] == "exported"
    assert line["type"]  == "tx"


# ── POST /api/labels/import ───────────────────────────────────────────────────

def test_import_labels(client):
    jsonl = '{"type":"tx","ref":"' + "a" * 64 + '","label":"imported"}'
    res   = client.post(
        "/api/labels/import",
        data         = jsonl,
        content_type = "application/x-ndjson",
    )
    assert res.status_code == 200
    assert res.get_json()["imported"] == 1


def test_import_then_tx_has_label(client):
    """Label imported via BIP-329 should appear on the tx graph node."""
    jsonl = '{"type":"tx","ref":"' + MOCK_TXID + '","label":"from sparrow"}'
    client.post(
        "/api/labels/import",
        data         = jsonl,
        content_type = "application/x-ndjson",
    )
    res = client.get(f"/api/tx?txid={MOCK_TXID}")
    tx  = res.get_json()["tx"]
    assert tx["label"] == "from sparrow"
