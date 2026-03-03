from abc import ABC, abstractmethod
from typing import Any

class NodeAdapter(ABC):
    @abstractmethod
    def get_raw_transaction(self, txid: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def get_block_height(self) -> int:
        ...
