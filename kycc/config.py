import os
import tomllib
from dataclasses import dataclass


@dataclass
class Config:
    node_type: str
    node_host: str
    node_port: int
    node_user: str
    node_password: str
    node_cookie_file: str
    node_network: str
    server_host: str
    server_port: int
    server_debug: bool
    db_path: str


def load_config(path: str = "kycc.toml") -> Config:
    """
    Load configuration with env var overrides.

    Priority: environment variable > kycc.toml > built-in default.
    The toml file is optional — all values can be supplied via env vars,
    which is the recommended approach for Docker deployments.
    """
    raw: dict = {}
    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except FileNotFoundError:
        pass  # fine — env vars can supply everything

    node = raw.get("node", {})
    server = raw.get("server", {})
    db = raw.get("db", {})

    return Config(
        node_type=os.environ.get("KYCC_NODE_TYPE", node.get("type", "bitcoincore")),
        node_host=os.environ.get("KYCC_NODE_HOST", node.get("host", "127.0.0.1")),
        node_port=int(os.environ.get("KYCC_NODE_PORT", node.get("port", 8332))),
        node_user=os.environ.get("KYCC_NODE_USER", node.get("user", "")),
        node_password=os.environ.get("KYCC_NODE_PASSWORD", node.get("password", "")),
        node_cookie_file=os.environ.get(
            "KYCC_NODE_COOKIE_FILE", node.get("cookie_file", "")
        ),
        node_network=os.environ.get(
            "KYCC_NODE_NETWORK", node.get("network", "mainnet")
        ),
        server_host=os.environ.get("KYCC_SERVER_HOST", server.get("host", "0.0.0.0")),
        server_port=int(os.environ.get("KYCC_SERVER_PORT", server.get("port", 5050))),
        server_debug=os.environ.get(
            "KYCC_SERVER_DEBUG", str(server.get("debug", False))
        ).lower()
        == "true",
        db_path=os.environ.get("KYCC_DB_PATH", db.get("path", "kycc.db")),
    )
