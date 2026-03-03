from flask import Blueprint, current_app, jsonify

bp = Blueprint("health", __name__)

# Map config key → annotation codes it can produce
HEURISTIC_META: dict[str, dict] = {
    "rbf": {
        "display": "RBF Signaling",
        "codes": ["RBF_SIGNALING"],
        "desc": "Transaction signals Replace-By-Fee (BIP-125).",
    },
    "locktime": {
        "display": "Locktime Pattern",
        "codes": ["ANTI_FEE_SNIPING", "TIMELOCK_UNIX"],
        "desc": "Locktime set to block height or Unix timestamp.",
    },
    "address_reuse": {
        "display": "Address Reuse",
        "codes": ["ADDRESS_REUSE"],
        "desc": "An address appears in both inputs and outputs.",
    },
    "round_payment": {
        "display": "Round Payment",
        "codes": ["ROUND_PAYMENT"],
        "desc": "Output value is a round number — likely the payment, not change.",
    },
    "change_inference": {
        "display": "Change Detection",
        "codes": ["PROBABLE_CHANGE"],
        "desc": "Probable change output identified by script type match.",
    },
    "script_mismatch": {
        "display": "Script Type Mismatch",
        "codes": ["SCRIPT_TYPE_MISMATCH"],
        "desc": "Mixed script types across inputs/outputs.",
    },
    "consolidation": {
        "display": "Consolidation",
        "codes": ["CONSOLIDATION"],
        "desc": "3+ inputs → ≤2 outputs — likely a UTXO management self-spend.",
    },
    "uioh": {
        "display": "UIOH",
        "codes": ["UIOH"],
        "desc": (
            "Largest input alone could fund all outputs"
            " — unnecessary inputs present."
        ),
    },
}


@bp.get("/api/health")
def health():
    adapter = current_app.config["NODE_ADAPTER"]
    cfg = current_app.config["KYCC_CONFIG"]
    enabled_keys: list[str] = current_app.config.get(
        "ENABLED_HEURISTICS", list(HEURISTIC_META)
    )

    try:
        block_height = adapter.get_block_height()
        node_online = True
    except Exception:
        block_height = None
        node_online = False

    heuristics = [
        {
            "key": k,
            "display": HEURISTIC_META[k]["display"],
            "codes": HEURISTIC_META[k]["codes"],
            "desc": HEURISTIC_META[k]["desc"],
            "enabled": k in enabled_keys,
        }
        for k in HEURISTIC_META
    ]

    return jsonify(
        {
            "ok": True,
            "version": "0.1.0",
            "node_type": cfg.node_type,
            "network": cfg.node_network,
            "node_host": cfg.node_host,
            "node_port": cfg.node_port,
            "block_height": block_height,
            "node_online": node_online,
            "heuristics": heuristics,
        }
    )
