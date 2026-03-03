from typing import Any
from bitcoinrpc.authproxy import AuthServiceProxy
from kycc.adapters.base import NodeAdapter


class BitcoinCoreAdapter(NodeAdapter):
    def __init__(self, host: str, port: int, user: str, password: str):
        url = f"http://{user}:{password}@{host}:{port}"
        self._rpc = AuthServiceProxy(url)

    def get_raw_transaction(self, txid: str) -> dict[str, Any]:
        return self._rpc.getrawtransaction(txid, 2)

    def get_block_height(self) -> int:
        return self._rpc.getblockcount()

    def get_address_history(self, address: str) -> list[dict]:
        result = self._rpc.scantxoutset("start", [f"addr({address})"])
        return [
            {"tx_hash": u["txid"], "height": u.get("height", 0)}
            for u in result.get("unspents", [])
        ]
