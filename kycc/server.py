from flask import Flask
from kycc.config import load_config
from kycc.labels.store import LabelStore
from kycc.fingerprint.engine import FingerprintEngine


def create_app(config_path: str = "kycc.toml") -> Flask:
    app = Flask(__name__)
    cfg = load_config(config_path)

    # ── persistence ───────────────────────────────────────────────
    store = LabelStore(cfg.db_path)
    app.config["LABEL_STORE"] = store

    # ── node adapter ──────────────────────────────────────────────
    adapter = _make_adapter(cfg)
    app.config["NODE_ADAPTER"] = adapter

    # ── fingerprint engine ────────────────────────────────────────
    engine = FingerprintEngine()
    app.config["FINGERPRINT_ENGINE"] = engine

    # ── blueprints ────────────────────────────────────────────────
    from kycc.routes.health  import bp as health_bp
    from kycc.routes.tx      import bp as tx_bp
    from kycc.routes.labels  import bp as labels_bp
    from kycc.routes.export  import bp as export_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(tx_bp)
    app.register_blueprint(labels_bp)
    app.register_blueprint(export_bp)

    return app


def _make_adapter(cfg):
    if cfg.node_type == "bitcoincore":
        from kycc.adapters.bitcoincore import BitcoinCoreAdapter
        return BitcoinCoreAdapter(
            host     = cfg.node_host,
            port     = cfg.node_port,
            user     = cfg.node_user,
            password = cfg.node_password,
        )
    raise ValueError(f"Unknown node type: {cfg.node_type}")
