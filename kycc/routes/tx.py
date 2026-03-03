from flask import Blueprint, request, jsonify, current_app
from kycc.graph.parser import parse_tx
from kycc.graph.serializer import tx_to_dict

bp = Blueprint("tx", __name__)


@bp.get("/api/tx")
def get_tx():
    txid = request.args.get("txid", "").strip()
    if not txid or len(txid) != 64:
        return jsonify({
            "ok": False,
            "error": "txid must be a 64-character hex string"
        }), 400

    adapter  = current_app.config["NODE_ADAPTER"]
    store    = current_app.config["LABEL_STORE"]
    engine   = current_app.config["FINGERPRINT_ENGINE"]

    try:
        raw = adapter.get_raw_transaction(txid)
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Node RPC error: {str(e)}"
        }), 502

    # parse → hydrate labels → annotate
    tx = parse_tx(raw)

    tx.label = store.hydrate_tx(tx.txid)
    for u in tx.inputs:
        u.label = store.hydrate_utxo(u.txid, u.vout)
    for u in tx.outputs:
        u.label = store.hydrate_utxo(tx.txid, u.vout)

    engine.annotate_inplace(tx)

    return jsonify({"ok": True, "tx": tx_to_dict(tx)})
