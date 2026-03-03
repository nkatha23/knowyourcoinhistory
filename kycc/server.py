import tomllib

from flask import Flask

from kycc.config import load_config
from kycc.fingerprint.engine import DETECTOR_MAP, FingerprintEngine
from kycc.labels.store import LabelStore


def create_app(config_path: str = "kycc.toml") -> Flask:
    app = Flask(__name__)
    cfg = load_config(config_path)

    # Store config so routes can read node_type, network, etc.
    app.config["KYCC_CONFIG"] = cfg

    store = LabelStore(cfg.db_path)
    app.config["LABEL_STORE"] = store

    adapter = _make_adapter(cfg)
    app.config["NODE_ADAPTER"] = adapter

    # Load enabled heuristics from toml (fall back to all if not set)
    enabled = _load_heuristics(config_path)
    app.config["ENABLED_HEURISTICS"] = enabled
    engine = FingerprintEngine(enabled=enabled if enabled else None)
    app.config["FINGERPRINT_ENGINE"] = engine

    from kycc.routes.address import bp as address_bp
    from kycc.routes.export import bp as export_bp
    from kycc.routes.health import bp as health_bp
    from kycc.routes.labels import bp as labels_bp
    from kycc.routes.session import bp as session_bp
    from kycc.routes.tx import bp as tx_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(tx_bp)
    app.register_blueprint(labels_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(address_bp)

    return app


def _load_heuristics(config_path: str) -> list[str]:
    try:
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)
        heuristics = raw.get("fingerprint", {}).get("heuristics", [])
        # Only include keys that exist in the detector map
        return [h for h in heuristics if h in DETECTOR_MAP]
    except Exception:
        return list(DETECTOR_MAP.keys())


def _make_adapter(cfg):
    if cfg.node_type == "bitcoincore":
        from kycc.adapters.bitcoincore import BitcoinCoreAdapter

        return BitcoinCoreAdapter(
            host=cfg.node_host,
            port=cfg.node_port,
            user=cfg.node_user,
            password=cfg.node_password,
        )
    if cfg.node_type == "electrum":
        from kycc.adapters.electrum import ElectrumAdapter

        return ElectrumAdapter(host=cfg.node_host, port=cfg.node_port)
    raise ValueError(f"Unknown node type: {cfg.node_type}")
