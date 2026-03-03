from dataclasses import dataclass, field
from typing import Literal, Optional

ScriptType = Literal[
    "p2pkh",
    "p2sh",
    "p2wpkh",
    "p2wsh",
    "p2tr",
    "p2sh-p2wpkh",
    "coinbase",
    "op_return",
    "unknown",
]

LockTimeType = Literal["none", "block_height", "unix_timestamp"]


@dataclass
class UTXONode:
    txid: str
    vout: int
    value_sats: int
    script_pubkey_hex: str
    script_type: ScriptType
    address: Optional[str]
    is_spent: bool
    spending_txid: Optional[str]
    label: Optional[str] = None


@dataclass
class HeuristicResult:
    code: str
    severity: Literal["info", "warning", "flag"]
    description: str
    affected: list[str] = field(default_factory=list)


@dataclass
class TxNode:
    txid: str
    block_height: Optional[int]
    block_hash: Optional[str]
    fee_sats: Optional[int]
    is_coinbase: bool
    is_rbf: bool
    locktime: int
    locktime_type: LockTimeType
    version: int
    size: int
    weight: int
    inputs: list[UTXONode]
    outputs: list[UTXONode]
    label: Optional[str] = None
    annotations: list[HeuristicResult] = field(default_factory=list)


@dataclass
class GraphSession:
    session_id: str
    wallet_ids: list[str]
    loaded_txids: set[str]
    root_txid: str
