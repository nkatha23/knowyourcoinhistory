"""
Convert TxNode / UTXONode dataclasses to JSON-serializable dicts.
Called by route handlers before jsonify().
"""

from kycc.graph.models import TxNode, UTXONode


def utxo_to_dict(u: UTXONode) -> dict:
    return {
        "txid": u.txid,
        "vout": u.vout,
        "value_sats": u.value_sats,
        "value_btc": round(u.value_sats / 1e8, 8),
        "script_pubkey_hex": u.script_pubkey_hex,
        "script_type": u.script_type,
        "address": u.address,
        "is_spent": u.is_spent,
        "spending_txid": u.spending_txid,
        "label": u.label,
    }


def tx_to_dict(tx: TxNode) -> dict:
    return {
        "txid": tx.txid,
        "block_height": tx.block_height,
        "block_hash": tx.block_hash,
        "fee_sats": tx.fee_sats,
        "fee_btc": round(tx.fee_sats / 1e8, 8) if tx.fee_sats else None,
        "is_coinbase": tx.is_coinbase,
        "is_rbf": tx.is_rbf,
        "locktime": tx.locktime,
        "locktime_type": tx.locktime_type,
        "version": tx.version,
        "size": tx.size,
        "weight": tx.weight,
        "inputs": [utxo_to_dict(u) for u in tx.inputs],
        "outputs": [utxo_to_dict(u) for u in tx.outputs],
        "label": tx.label,
        "annotations": [
            {
                "code": a.code,
                "severity": a.severity,
                "description": a.description,
                "affected": a.affected,
            }
            for a in tx.annotations
        ],
    }
