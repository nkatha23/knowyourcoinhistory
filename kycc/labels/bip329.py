"""
BIP-329 wallet label import/export.
Format: one JSON object per line (.jsonl)
Spec: https://github.com/bitcoin/bips/blob/master/bip-0329.mediawiki
"""
import json
import time
from typing import Iterator
from kycc.labels.store import Label, LabelStore, RefType

VALID_TYPES: set[str] = {"tx", "utxo", "addr", "xpub"}


def serialize(store: LabelStore, wallet_id: str = "default") -> str:
    """Export all labels for a wallet as a BIP-329 .jsonl string."""
    lines = []
    for lbl in store.list(wallet_id=wallet_id):
        entry: dict = {
            "type":  lbl.ref_type,
            "ref":   lbl.ref,
            "label": lbl.label,
        }
        if lbl.spendable is not None:
            entry["spendable"] = lbl.spendable
        lines.append(json.dumps(entry, ensure_ascii=False))
    return "\n".join(lines)


def deserialize(
    jsonl: str,
    wallet_id: str = "default",
    origin: str = "bip329_import",
) -> list[Label]:
    """Parse a BIP-329 .jsonl string into a list of Label objects."""
    labels = []
    for lineno, line in enumerate(jsonl.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"BIP-329 parse error on line {lineno}: {e}") from e

        ref_type = entry.get("type", "")
        if ref_type not in VALID_TYPES:
            raise ValueError(
                f"BIP-329 line {lineno}: invalid type '{ref_type}'. "
                f"Must be one of {VALID_TYPES}"
            )

        ref = entry.get("ref", "").strip()
        if not ref:
            raise ValueError(f"BIP-329 line {lineno}: 'ref' is empty")

        label_text = entry.get("label", "").strip()
        if not label_text:
            raise ValueError(f"BIP-329 line {lineno}: 'label' is empty")

        spendable_raw = entry.get("spendable")
        spendable = bool(spendable_raw) if spendable_raw is not None else None

        now = int(time.time())
        labels.append(Label(
            wallet_id  = wallet_id,
            ref_type   = ref_type,
            ref        = ref,
            label      = label_text,
            origin     = origin,
            spendable  = spendable,
            created_at = now,
            updated_at = now,
        ))
    return labels


def import_to_store(
    jsonl: str,
    store: LabelStore,
    wallet_id: str = "default",
) -> int:
    """Parse and upsert all labels. Returns count of labels imported."""
    labels = deserialize(jsonl, wallet_id=wallet_id)
    for lbl in labels:
        store.upsert(lbl)
    return len(labels)
