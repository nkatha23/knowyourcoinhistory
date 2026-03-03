from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("address", __name__)


@bp.get("/api/address")
def get_address_history():
    address = request.args.get("address", "").strip()
    if not address:
        return jsonify({"ok": False, "error": "address is required"}), 400

    adapter = current_app.config["NODE_ADAPTER"]
    store = current_app.config["LABEL_STORE"]
    wallet_id = request.args.get("wallet_id", "default")

    try:
        history = adapter.get_address_history(address)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Node error: {str(e)}"}), 502

    # Hydrate each tx with its label if one exists
    enriched = []
    for entry in history:
        tx_hash = entry.get("tx_hash") or entry.get("txid", "")
        label = store.hydrate_tx(tx_hash, wallet_id) if tx_hash else None
        enriched.append({**entry, "label": label})

    return jsonify(
        {
            "ok": True,
            "address": address,
            "history": enriched,
            "count": len(enriched),
        }
    )
