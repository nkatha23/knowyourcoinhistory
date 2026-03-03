from flask import Blueprint, current_app, jsonify, request

from kycc.labels.store import Label

bp = Blueprint("labels", __name__)


@bp.get("/api/labels")
def list_labels():
    store = current_app.config["LABEL_STORE"]
    wallet_id = request.args.get("wallet_id", "default")
    ref_type = request.args.get("ref_type")

    labels = store.list(wallet_id=wallet_id, ref_type=ref_type)
    return jsonify(
        {
            "ok": True,
            "labels": [_label_to_dict(lbl) for lbl in labels],
            "count": len(labels),
        }
    )


@bp.get("/api/wallets")
def list_wallets():
    store = current_app.config["LABEL_STORE"]
    return jsonify({"ok": True, "wallets": store.list_wallets()})


@bp.post("/api/label")
def upsert_label():
    store = current_app.config["LABEL_STORE"]
    data = request.get_json(silent=True) or {}

    ref_type = data.get("ref_type", "").strip()
    ref = data.get("ref", "").strip()
    label_txt = data.get("label", "").strip()
    wallet_id = data.get("wallet_id", "default").strip()
    spendable = data.get("spendable")

    if ref_type not in ("tx", "utxo", "addr", "xpub"):
        return jsonify({"ok": False, "error": f"Invalid ref_type '{ref_type}'"}), 400
    if not ref:
        return jsonify({"ok": False, "error": "ref is required"}), 400
    if not label_txt:
        return jsonify({"ok": False, "error": "label is required"}), 400

    store.upsert(
        Label(
            wallet_id=wallet_id,
            ref_type=ref_type,
            ref=ref,
            label=label_txt,
            spendable=bool(spendable) if spendable is not None else None,
        )
    )

    return jsonify({"ok": True, "ref": ref, "label": label_txt})


@bp.delete("/api/label")
def delete_label():
    store = current_app.config["LABEL_STORE"]
    data = request.get_json(silent=True) or {}

    ref_type = data.get("ref_type", "").strip()
    ref = data.get("ref", "").strip()
    wallet_id = data.get("wallet_id", "default").strip()

    if not ref_type or not ref:
        return jsonify({"ok": False, "error": "ref_type and ref are required"}), 400

    store.delete(ref_type, ref, wallet_id)
    return jsonify({"ok": True, "deleted": ref})


def _label_to_dict(lbl) -> dict:
    return {
        "wallet_id": lbl.wallet_id,
        "ref_type": lbl.ref_type,
        "ref": lbl.ref,
        "label": lbl.label,
        "origin": lbl.origin,
        "spendable": lbl.spendable,
        "created_at": lbl.created_at,
        "updated_at": lbl.updated_at,
    }
