from typing import Optional
from kycc.graph.models import TxNode, UTXONode
from kycc.fingerprint.models import HeuristicResult


def detect_rbf(tx: TxNode) -> Optional[HeuristicResult]:
    if tx.is_rbf:
        return HeuristicResult(
            code="RBF_SIGNALING", severity="info",
            description="Transaction signals Replace-By-Fee (BIP-125). "
                        "The sender can bump the fee before confirmation.",
        )
    return None


def detect_locktime(tx: TxNode) -> Optional[HeuristicResult]:
    if tx.locktime_type == "none":
        return None
    if tx.locktime_type == "block_height":
        return HeuristicResult(
            code="ANTI_FEE_SNIPING", severity="info",
            description=f"Locktime {tx.locktime} set to a block height. "
                        "Consistent with anti-fee-sniping (Bitcoin Core, Electrum).",
        )
    if tx.locktime_type == "unix_timestamp":
        return HeuristicResult(
            code="TIMELOCK_UNIX", severity="info",
            description=f"Locktime {tx.locktime} is a Unix timestamp. "
                        "Transaction cannot be mined before that time.",
        )
    return None


def detect_address_reuse(tx: TxNode) -> Optional[HeuristicResult]:
    input_addresses  = {u.address for u in tx.inputs  if u.address}
    output_addresses = {u.address for u in tx.outputs if u.address}
    reused = input_addresses & output_addresses
    if reused:
        return HeuristicResult(
            code="ADDRESS_REUSE", severity="flag",
            description="One or more addresses appear in both inputs and outputs. "
                        "Address reuse degrades privacy for sender and receiver.",
            affected=sorted(reused),
        )
    return None


ROUND_THRESHOLDS = [1_000, 10_000, 100_000, 1_000_000, 10_000_000]

def detect_round_payment(tx: TxNode) -> Optional[HeuristicResult]:
    if tx.is_coinbase:
        return None
    flagged = []
    for out in tx.outputs:
        if any(out.value_sats % t == 0 for t in ROUND_THRESHOLDS):
            flagged.append(f"{tx.txid}:{out.vout} ({out.value_sats} sats)")
    if flagged:
        return HeuristicResult(
            code="ROUND_PAYMENT", severity="info",
            description="Output(s) with round values detected. "
                        "Round amounts are likely payment outputs, not change.",
            affected=flagged,
        )
    return None


def detect_change_output(tx: TxNode) -> Optional[HeuristicResult]:
    if tx.is_coinbase or len(tx.outputs) != 2:
        return None
    input_types = {u.script_type for u in tx.inputs
                   if u.script_type not in ("coinbase", "unknown")}
    if len(input_types) != 1:
        return None
    input_type = next(iter(input_types))
    change_candidates = [o for o in tx.outputs if o.script_type == input_type]
    if len(change_candidates) == 1:
        c = change_candidates[0]
        return HeuristicResult(
            code="PROBABLE_CHANGE", severity="info",
            description=f"Output {c.vout} ({c.value_sats} sats, {c.script_type}) "
                        "likely change — script type matches all inputs.",
            affected=[f"{tx.txid}:{c.vout}"],
        )
    return None


def detect_script_mismatch(tx: TxNode) -> Optional[HeuristicResult]:
    if tx.is_coinbase:
        return None
    input_types  = {u.script_type for u in tx.inputs
                    if u.script_type not in ("coinbase", "unknown")}
    output_types = {u.script_type for u in tx.outputs
                    if u.script_type not in ("op_return", "unknown")}
    all_types = input_types | output_types
    if len(all_types) > 1:
        return HeuristicResult(
            code="SCRIPT_TYPE_MISMATCH", severity="warning",
            description=f"Mixed script types across inputs/outputs: "
                        f"{', '.join(sorted(all_types))}. "
                        "May indicate wallet migration or a multi-party transaction.",
            affected=sorted(all_types),
        )
    return None


def detect_consolidation(tx: TxNode) -> Optional[HeuristicResult]:
    if tx.is_coinbase:
        return None
    if len(tx.inputs) >= 3 and len(tx.outputs) <= 2:
        return HeuristicResult(
            code="CONSOLIDATION", severity="info",
            description=f"{len(tx.inputs)} inputs consolidated into "
                        f"{len(tx.outputs)} output(s). "
                        "Likely a UTXO management self-spend.",
        )
    return None


def detect_uioh(tx: TxNode) -> Optional[HeuristicResult]:
    if tx.is_coinbase or len(tx.inputs) < 2:
        return None
    output_total  = sum(o.value_sats for o in tx.outputs)
    fee_headroom  = (tx.fee_sats or 0) * 2
    required      = output_total + fee_headroom
    largest_input = max(u.value_sats for u in tx.inputs)
    if largest_input >= required:
        return HeuristicResult(
            code="UIOH", severity="warning",
            description=f"Largest input ({largest_input} sats) alone could fund "
                        f"all outputs + fees ({required} sats). "
                        "Additional inputs were unnecessary — possible CoinJoin "
                        "or suboptimal coin selection.",
        )
    return None
