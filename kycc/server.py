import os
import tomllib

from flask import Flask, send_from_directory

from kycc.config import load_config
from kycc.fingerprint.engine import DETECTOR_MAP, FingerprintEngine
from kycc.labels.store import LabelStore

# Absolute path to the React production build.
# In development, Vite runs separately and this directory may not exist.
# In Docker, the frontend stage copies web/dist here before the image starts.
_STATIC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "web", "dist"))


def create_app(config_path: str = "kycc.toml") -> Flask:
    app = Flask(__name__, static_folder=_STATIC_DIR, static_url_path="")
    cfg = load_config(config_path)

    app.config["KYCC_CONFIG"] = cfg

    store = LabelStore(cfg.db_path)
    app.config["LABEL_STORE"] = store

    adapter = _make_adapter(cfg)
    app.config["NODE_ADAPTER"] = adapter

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

    # Serve the React SPA for all non-API routes.
    # This only matters in production (Docker); in dev, Vite handles the frontend.
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path: str):
        # If the path matches a real file in web/dist (JS, CSS, assets), serve it.
        # Otherwise fall back to index.html so React Router can handle the route.
        file_path = os.path.join(app.static_folder, path)
        if path and os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

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
