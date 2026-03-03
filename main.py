from kycc.server import create_app
from kycc.config import load_config

if __name__ == "__main__":
    cfg = load_config()
    app = create_app()
    app.run(host=cfg.server_host, port=cfg.server_port, debug=cfg.server_debug)
