from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response, current_app
from kycc.labels.bip329 import serialize, import_to_store

bp = Blueprint("export", __name__)


@bp.get("/api/labels/export")
def export_labels():
    store     = current_app.config["LABEL_STORE"]
    wallet_id = request.args.get("wallet_id", "default")

    jsonl     = serialize(store, wallet_id=wallet_id)
    date_str  = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename  = f"kycc-labels-{wallet_id}-{date_str}.jsonl"

    return Response(
        jsonl,
        mimetype    = "application/x-ndjson",
        headers     = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@bp.post("/api/labels/import")
def import_labels():
    store     = current_app.config["LABEL_STORE"]
    wallet_id = request.args.get("wallet_id", "default")

    # accept raw .jsonl body or multipart file upload
    if request.content_type and "multipart" in request.content_type:
        f = request.files.get("file")
        if not f:
            return jsonify({"ok": False, "error": "No file uploaded"}), 400
        jsonl = f.read().decode("utf-8")
    else:
        jsonl = request.get_data(as_text=True)

    if not jsonl.strip():
        return jsonify({"ok": False, "error": "Empty body"}), 400

    try:
        count = import_to_store(jsonl, store, wallet_id=wallet_id)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 422

    return jsonify({"ok": True, "imported": count, "wallet_id": wallet_id})
