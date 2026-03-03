from abc import ABC, abstractmethod
from typing import Any


class NodeAdapter(ABC):

    @abstractmethod
    def get_raw_transaction(self, txid: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_block_height(self) -> int: ...

    def get_address_history(self, address: str) -> list[dict]:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support address history"
        )
