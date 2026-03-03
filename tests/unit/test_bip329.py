import tempfile

import pytest

from kycc.labels.bip329 import deserialize, import_to_store, serialize
from kycc.labels.store import LabelStore


def make_store():
    return LabelStore(tempfile.mktemp(suffix=".db"))


SAMPLE_JSONL = "\n".join(
    [
        '{"type":"tx",   "ref":"' + "a" * 64 + '", "label":"Exchange withdrawal"}',
        '{"type":"utxo", "ref":"' + "b" * 64 + ':0", "label":"KYC tainted"}',
        '{"type":"addr", "ref":"bc1qtest", "label":"Cold storage"}',
        '{"type":"xpub", "ref":"xpubTEST", "label":"Ledger"}',
    ]
)


def test_deserialize_all_ref_types():
    labels = deserialize(SAMPLE_JSONL)
    assert len(labels) == 4
    types = {lbl.ref_type for lbl in labels}
    assert types == {"tx", "utxo", "addr", "xpub"}


def test_deserialize_sets_wallet_id():
    labels = deserialize(SAMPLE_JSONL, wallet_id="my_wallet")
    assert all(lbl.wallet_id == "my_wallet" for lbl in labels)


def test_deserialize_sets_origin():
    labels = deserialize(SAMPLE_JSONL, origin="bip329_import")
    assert all(lbl.origin == "bip329_import" for lbl in labels)


def test_roundtrip():
    store = make_store()
    import_to_store(SAMPLE_JSONL, store)
    exported = serialize(store)
    labels_back = deserialize(exported)
    assert len(labels_back) == 4


def test_import_returns_count():
    store = make_store()
    count = import_to_store(SAMPLE_JSONL, store)
    assert count == 4


def test_import_idempotent():
    store = make_store()
    import_to_store(SAMPLE_JSONL, store)
    import_to_store(SAMPLE_JSONL, store)  # second import — same data
    assert len(store.list()) == 4  # no duplicates


def test_invalid_type_raises():
    bad = '{"type":"invoice","ref":"abc","label":"test"}'
    with pytest.raises(ValueError, match="invalid type"):
        deserialize(bad)


def test_empty_ref_raises():
    bad = '{"type":"tx","ref":"","label":"test"}'
    with pytest.raises(ValueError, match="'ref' is empty"):
        deserialize(bad)


def test_empty_label_raises():
    bad = '{"type":"tx","ref":"' + "a" * 64 + '","label":""}'
    with pytest.raises(ValueError, match="'label' is empty"):
        deserialize(bad)


def test_malformed_json_raises():
    with pytest.raises(ValueError, match="BIP-329 parse error"):
        deserialize('{"type":"tx", bad json}')


def test_empty_lines_ignored():
    jsonl = "\n\n" + '{"type":"tx","ref":"' + "a" * 64 + '","label":"ok"}' + "\n\n"
    labels = deserialize(jsonl)
    assert len(labels) == 1


def test_spendable_field_preserved():
    jsonl = (
        '{"type":"utxo","ref":"' + "a" * 64 + ':0","label":"test","spendable":false}'
    )
    labels = deserialize(jsonl)
    assert labels[0].spendable is False
