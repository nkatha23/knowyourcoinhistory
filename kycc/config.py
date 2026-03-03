import tomllib
from pathlib import Path
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
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return Config(
        node_type=raw["node"]["type"],
        node_host=raw["node"]["host"],
        node_port=raw["node"]["port"],
        node_user=raw["node"].get("user", ""),
        node_password=raw["node"].get("password", ""),
        node_cookie_file=raw["node"].get("cookie_file", ""),
        node_network=raw["node"]["network"],
        server_host=raw["server"]["host"],
        server_port=raw["server"]["port"],
        server_debug=raw["server"]["debug"],
        db_path=raw["db"]["path"],
    )
