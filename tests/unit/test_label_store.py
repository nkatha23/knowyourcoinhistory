import tempfile

from kycc.labels.store import Label, LabelStore


def make_store():
    tmp = tempfile.mktemp(suffix=".db")
    return LabelStore(tmp), tmp


def test_upsert_and_get():
    store, _ = make_store()
    store.upsert(
        Label(
            wallet_id="default",
            ref_type="tx",
            ref="a" * 64,
            label="Exchange withdrawal",
        )
    )
    result = store.get("tx", "a" * 64)
    assert result is not None
    assert result.label == "Exchange withdrawal"


def test_upsert_updates_existing():
    store, _ = make_store()
    store.upsert(Label(wallet_id="default", ref_type="tx", ref="a" * 64, label="first"))
    store.upsert(
        Label(wallet_id="default", ref_type="tx", ref="a" * 64, label="updated")
    )
    assert store.get("tx", "a" * 64).label == "updated"


def test_delete():
    store, _ = make_store()
    store.upsert(Label(wallet_id="default", ref_type="tx", ref="a" * 64, label="test"))
    store.delete("tx", "a" * 64)
    assert store.get("tx", "a" * 64) is None


def test_list_all():
    store, _ = make_store()
    store.upsert(
        Label(wallet_id="default", ref_type="tx", ref="a" * 64, label="tx label")
    )
    store.upsert(Label(wallet_id="default", ref_type="addr", ref="bc1q", label="cold"))
    assert len(store.list()) == 2


def test_list_filtered_by_ref_type():
    store, _ = make_store()
    store.upsert(Label(wallet_id="default", ref_type="tx", ref="a" * 64, label="tx"))
    store.upsert(Label(wallet_id="default", ref_type="addr", ref="bc1q", label="addr"))
    assert len(store.list(ref_type="tx")) == 1
    assert len(store.list(ref_type="addr")) == 1


def test_wallet_id_isolation():
    store, _ = make_store()
    store.upsert(
        Label(wallet_id="wallet_a", ref_type="tx", ref="a" * 64, label="from a")
    )
    store.upsert(
        Label(wallet_id="wallet_b", ref_type="tx", ref="a" * 64, label="from b")
    )
    assert store.get("tx", "a" * 64, wallet_id="wallet_a").label == "from a"
    assert store.get("tx", "a" * 64, wallet_id="wallet_b").label == "from b"


def test_hydrate_tx():
    store, _ = make_store()
    store.upsert(
        Label(wallet_id="default", ref_type="tx", ref="a" * 64, label="hydrated")
    )
    assert store.hydrate_tx("a" * 64) == "hydrated"
    assert store.hydrate_tx("b" * 64) is None


def test_hydrate_utxo():
    store, _ = make_store()
    store.upsert(
        Label(wallet_id="default", ref_type="utxo", ref="a" * 64 + ":0", label="dust")
    )
    assert store.hydrate_utxo("a" * 64, 0) == "dust"
    assert store.hydrate_utxo("a" * 64, 1) is None
