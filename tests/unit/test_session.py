import pytest
from unittest.mock import MagicMock
from flask import Flask
from kycc.routes.health  import bp as health_bp
from kycc.routes.tx      import bp as tx_bp
from kycc.routes.labels  import bp as labels_bp
from kycc.routes.export  import bp as export_bp
from kycc.routes.session import bp as session_bp
from kycc.labels.store   import LabelStore
from kycc.fingerprint.engine import FingerprintEngine
import tempfile

MOCK_TXID = "a" * 64


def _make_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["NODE_ADAPTER"]       = MagicMock()
    app.config["LABEL_STORE"]        = LabelStore(tempfile.mktemp(suffix=".db"))
    app.config["FINGERPRINT_ENGINE"] = FingerprintEngine()
    for bp in [health_bp, tx_bp, labels_bp, export_bp, session_bp]:
        app.register_blueprint(bp)
    return app


@pytest.fixture
def client():
    with _make_app().test_client() as c:
        yield c


def test_create_session(client):
    res  = client.post("/api/session", json={"root_txid": MOCK_TXID, "wallet_ids": ["default"]})
    data = res.get_json()
    assert res.status_code   == 200
    assert data["ok"]         is True
    assert "session_id"       in data
    assert data["root_txid"]  == MOCK_TXID


def test_create_session_invalid_txid(client):
    res = client.post("/api/session", json={"root_txid": "tooshort", "wallet_ids": ["default"]})
    assert res.status_code == 400


def test_create_session_empty_wallets(client):
    res = client.post("/api/session", json={"root_txid": MOCK_TXID, "wallet_ids": []})
    assert res.status_code == 400


def test_get_session_roundtrip(client):
    create     = client.post("/api/session", json={"root_txid": MOCK_TXID, "wallet_ids": ["wallet_a", "wallet_b"]}).get_json()
    session_id = create["session_id"]
    res        = client.get(f"/api/session/{session_id}")
    data       = res.get_json()
    assert res.status_code    == 200
    assert data["session_id"] == session_id
    assert "wallet_a" in data["wallet_ids"]
    assert "wallet_b" in data["wallet_ids"]


def test_get_session_not_found(client):
    assert client.get("/api/session/does-not-exist").status_code == 404


def test_list_sessions_empty(client):
    res = client.get("/api/sessions")
    assert res.get_json()["sessions"] == []


def test_list_sessions_after_create(client):
    client.post("/api/session", json={"root_txid": MOCK_TXID, "wallet_ids": ["default"]})
    res = client.get("/api/sessions")
    assert len(res.get_json()["sessions"]) == 1


def test_multi_wallet_labels_isolated(client):
    client.post("/api/label", json={"ref_type": "tx", "ref": MOCK_TXID, "label": "wallet A label", "wallet_id": "wallet_a"})
    client.post("/api/label", json={"ref_type": "tx", "ref": MOCK_TXID, "label": "wallet B label", "wallet_id": "wallet_b"})
    res_a = client.get("/api/labels?wallet_id=wallet_a").get_json()
    res_b = client.get("/api/labels?wallet_id=wallet_b").get_json()
    assert res_a["labels"][0]["label"] == "wallet A label"
    assert res_b["labels"][0]["label"] == "wallet B label"


def test_multi_wallet_same_ref_different_labels(client):
    client.post("/api/label", json={"ref_type": "tx", "ref": MOCK_TXID, "label": "exchange",  "wallet_id": "hot_wallet"})
    client.post("/api/label", json={"ref_type": "tx", "ref": MOCK_TXID, "label": "savings",   "wallet_id": "cold_wallet"})
    hot  = client.get("/api/labels?wallet_id=hot_wallet").get_json()
    cold = client.get("/api/labels?wallet_id=cold_wallet").get_json()
    assert hot["labels"][0]["label"]  == "exchange"
    assert cold["labels"][0]["label"] == "savings"


