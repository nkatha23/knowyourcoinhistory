from typing import Any

from kycc.graph.models import TxNode, UTXONode
from kycc.script_utils import classify_script, is_rbf, locktime_type


def parse_tx(raw: dict[str, Any]) -> TxNode:
    vin = raw.get("vin", [])
    vout = raw.get("vout", [])

    coinbase = "coinbase" in vin[0] if vin else False

    inputs = _parse_inputs(vin, coinbase)
    outputs = _parse_outputs(raw["txid"], vout)

    input_total = sum(u.value_sats for u in inputs)
    output_total = sum(u.value_sats for u in outputs)
    fee = (input_total - output_total) if not coinbase else None

    lt = raw.get("locktime", 0)

    return TxNode(
        txid=raw["txid"],
        block_height=raw.get("blockheight"),
        block_hash=raw.get("blockhash"),
        fee_sats=fee,
        is_coinbase=coinbase,
        is_rbf=is_rbf(vin),
        locktime=lt,
        locktime_type=locktime_type(lt),
        version=raw.get("version", 1),
        size=raw.get("size", 0),
        weight=raw.get("weight", 0),
        inputs=inputs,
        outputs=outputs,
    )


def _parse_inputs(vin: list[dict], coinbase: bool) -> list[UTXONode]:
    if coinbase:
        return [
            UTXONode(
                txid="0" * 64,
                vout=0xFFFFFFFF,
                value_sats=0,
                script_pubkey_hex="",
                script_type="coinbase",
                address=None,
                is_spent=True,
                spending_txid=None,
            )
        ]

    result = []
    for inp in vin:
        prevout = inp.get("prevout", {})
        spk = prevout.get("scriptPubKey", {})
        spk_hex = spk.get("hex", "")
        sats = round(prevout.get("value", 0) * 1e8)

        result.append(
            UTXONode(
                txid=inp["txid"],
                vout=inp["vout"],
                value_sats=sats,
                script_pubkey_hex=spk_hex,
                script_type=classify_script(spk_hex),
                address=spk.get("address"),
                is_spent=True,
                spending_txid=None,
            )
        )
    return result


def _parse_outputs(txid: str, vout: list[dict]) -> list[UTXONode]:
    result = []
    for out in vout:
        spk = out.get("scriptPubKey", {})
        spk_hex = spk.get("hex", "")
        sats = round(out.get("value", 0) * 1e8)

        result.append(
            UTXONode(
                txid=txid,
                vout=out["n"],
                value_sats=sats,
                script_pubkey_hex=spk_hex,
                script_type=classify_script(spk_hex),
                address=spk.get("address"),
                is_spent=False,
                spending_txid=None,
            )
        )
    return result
