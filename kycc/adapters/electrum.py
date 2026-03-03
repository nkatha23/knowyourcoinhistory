import hashlib
import json
import socket
import ssl
from typing import Any

from kycc.adapters.base import NodeAdapter


class ElectrumAdapter(NodeAdapter):
    def __init__(self, host: str, port: int, use_ssl: bool = True, timeout: int = 10):
        self._host = host
        self._port = port
        self._use_ssl = use_ssl
        self._timeout = timeout
        self._sock = None
        self._id = 0
        self._connect()

    def _connect(self) -> None:
        raw = socket.create_connection((self._host, self._port), timeout=self._timeout)
        if self._use_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self._sock = ctx.wrap_socket(raw, server_hostname=self._host)
        else:
            self._sock = raw

    def _reconnect(self) -> None:
        try:
            self._sock.close()
        except Exception:
            pass
        self._connect()

    def _call(self, method: str, params: list) -> Any:
        self._id += 1
        payload = (
            json.dumps({"id": self._id, "method": method, "params": params}) + "\n"
        )
        try:
            self._sock.sendall(payload.encode())
            return self._read_response()
        except (BrokenPipeError, ConnectionResetError, OSError):
            self._reconnect()
            self._sock.sendall(payload.encode())
            return self._read_response()

    def _read_response(self) -> Any:
        buf = b""
        while True:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("Electrum server closed connection")
            buf += chunk
            if b"\n" in buf:
                line = buf.split(b"\n")[0]
                resp = json.loads(line)
                if "error" in resp and resp["error"]:
                    raise RuntimeError(f"Electrum error: {resp['error']}")
                return resp.get("result")

    def get_raw_transaction(self, txid: str) -> dict[str, Any]:
        result = self._call("blockchain.transaction.get", [txid, True])
        if not isinstance(result, dict):
            raise ValueError(f"Unexpected response for txid {txid}: {result}")
        # Electrum verbose=True omits prevout data that Bitcoin Core verbose=2 includes.
        # Resolve each input's prevout with a second call so value_sats, script_type,
        # and address are populated — required for fee calculation and all heuristics.
        self._resolve_prevouts(result)
        return result

    def _resolve_prevouts(self, tx: dict[str, Any]) -> None:
        """Fetch and inject prevout data for every non-coinbase input."""
        for vin in tx.get("vin", []):
            if "coinbase" in vin:
                continue
            prev_txid: str | None = vin.get("txid")
            vout_index: int | None = vin.get("vout")
            if prev_txid is None or vout_index is None:
                continue
            try:
                prev_tx = self._call("blockchain.transaction.get", [prev_txid, True])
                if isinstance(prev_tx, dict):
                    vouts: list = prev_tx.get("vout", [])
                    if vout_index < len(vouts):
                        vin["prevout"] = vouts[vout_index]
            except Exception:
                # Leave prevout absent; parser will treat it as unknown/zero
                pass

    def get_block_height(self) -> int:
        result = self._call("blockchain.headers.subscribe", [])
        if isinstance(result, dict):
            return result.get("height", 0)
        return 0

    def get_address_history(self, address: str) -> list[dict]:
        scripthash = _address_to_scripthash(address)
        return self._call("blockchain.scripthash.get_history", [scripthash]) or []

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass


def _address_to_scripthash(address: str) -> str:
    h = hashlib.sha256(address.encode()).digest()
    return h[::-1].hex()
