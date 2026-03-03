import json
import time
import uuid
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("session", __name__)


@bp.post("/api/session")
def create_session():
    data       = request.get_json(silent=True) or {}
    root_txid  = data.get("root_txid", "").strip()
    wallet_ids = data.get("wallet_ids", ["default"])

    if not root_txid or len(root_txid) != 64:
        return jsonify({"ok": False, "error": "root_txid must be a 64-character hex string"}), 400

    if not isinstance(wallet_ids, list) or not wallet_ids:
        return jsonify({"ok": False, "error": "wallet_ids must be a non-empty list"}), 400

    session_id = str(uuid.uuid4())
    store      = current_app.config["LABEL_STORE"]

    with store._conn() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, wallet_ids, root_txid, created_at) VALUES (?,?,?,?)",
            (session_id, json.dumps(wallet_ids), root_txid, int(time.time()))
        )

    return jsonify({
        "ok": True, "session_id": session_id,
        "root_txid": root_txid, "wallet_ids": wallet_ids,
    })


@bp.get("/api/session/<session_id>")
def get_session(session_id: str):
    store = current_app.config["LABEL_STORE"]
    with store._conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()

    if not row:
        return jsonify({"ok": False, "error": f"Session {session_id} not found"}), 404

    return jsonify({
        "ok": True,
        "session_id": row["session_id"],
        "root_txid":  row["root_txid"],
        "wallet_ids": json.loads(row["wallet_ids"]),
        "created_at": row["created_at"],
    })


@bp.get("/api/sessions")
def list_sessions():
    store = current_app.config["LABEL_STORE"]
    with store._conn() as conn:
        rows = conn.execute(
            "SELECT session_id, root_txid, wallet_ids, created_at "
            "FROM sessions ORDER BY created_at DESC LIMIT 50"
        ).fetchall()

    return jsonify({
        "ok": True,
        "sessions": [
            {
                "session_id": r["session_id"],
                "root_txid":  r["root_txid"],
                "wallet_ids": json.loads(r["wallet_ids"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    })
