import pytest
from kycc.graph.models import TxNode, UTXONode
from kycc.fingerprint import heuristics as H
from kycc.fingerprint.engine import FingerprintEngine


# ── helpers ───────────────────────────────────────────────────────────────────

def make_utxo(txid="a"*64, vout=0, sats=100_000,
              spk="0014"+"a"*40, script_type="p2wpkh",
              address="bc1qinput", is_spent=True):
    return UTXONode(
        txid=txid, vout=vout, value_sats=sats,
        script_pubkey_hex=spk, script_type=script_type,
        address=address, is_spent=is_spent, spending_txid=None,
    )

def make_tx(
    inputs=None, outputs=None,
    is_rbf=False, locktime=0, locktime_type="none",
    is_coinbase=False, fee_sats=1000,
):
    inputs  = inputs  or [make_utxo(sats=100_000, address="bc1qin")]
    outputs = outputs or [make_utxo(sats=99_000,  address="bc1qout",
                                    is_spent=False)]
    return TxNode(
        txid="a"*64, block_height=800_000, block_hash="b"*64,
        fee_sats=fee_sats, is_coinbase=is_coinbase,
        is_rbf=is_rbf, locktime=locktime,
        locktime_type=locktime_type,
        version=2, size=141, weight=564,
        inputs=inputs, outputs=outputs,
    )


# ── RBF ──────────────────────────────────────────────────────────────────────

def test_rbf_triggers():
    tx = make_tx(is_rbf=True)
    assert H.detect_rbf(tx).code == "RBF_SIGNALING"

def test_rbf_no_trigger():
    tx = make_tx(is_rbf=False)
    assert H.detect_rbf(tx) is None


# ── LOCKTIME ─────────────────────────────────────────────────────────────────

def test_locktime_block_height():
    tx = make_tx(locktime=850_000, locktime_type="block_height")
    assert H.detect_locktime(tx).code == "ANTI_FEE_SNIPING"

def test_locktime_unix():
    tx = make_tx(locktime=1_700_000_000, locktime_type="unix_timestamp")
    assert H.detect_locktime(tx).code == "TIMELOCK_UNIX"

def test_locktime_none_no_trigger():
    tx = make_tx(locktime=0, locktime_type="none")
    assert H.detect_locktime(tx) is None


# ── ADDRESS REUSE ─────────────────────────────────────────────────────────────

def test_address_reuse_triggers():
    shared = "bc1qshared"
    inp = make_utxo(address=shared)
    out = make_utxo(address=shared, is_spent=False)
    tx  = make_tx(inputs=[inp], outputs=[out])
    result = H.detect_address_reuse(tx)
    assert result.code == "ADDRESS_REUSE"
    assert shared in result.affected

def test_address_reuse_no_trigger():
    tx = make_tx(
        inputs  = [make_utxo(address="bc1qinput")],
        outputs = [make_utxo(address="bc1qoutput", is_spent=False)],
    )
    assert H.detect_address_reuse(tx) is None


# ── ROUND PAYMENT ─────────────────────────────────────────────────────────────

def test_round_payment_triggers():
    out = make_utxo(sats=100_000, is_spent=False)  # exactly 0.001 BTC
    tx  = make_tx(outputs=[out])
    assert H.detect_round_payment(tx).code == "ROUND_PAYMENT"

def test_round_payment_no_trigger():
    out = make_utxo(sats=99_347, is_spent=False)   # not round
    tx  = make_tx(outputs=[out])
    assert H.detect_round_payment(tx) is None

def test_round_payment_skips_coinbase():
    tx = make_tx(is_coinbase=True)
    assert H.detect_round_payment(tx) is None


# ── CHANGE OUTPUT INFERENCE ───────────────────────────────────────────────────

def test_change_inference_triggers():
    inp  = make_utxo(script_type="p2wpkh", sats=100_000, address="bc1qin")
    pay  = make_utxo(script_type="p2tr",   sats=60_000,  address="bc1pout", is_spent=False)
    chg  = make_utxo(script_type="p2wpkh", sats=39_000,  address="bc1qchg", is_spent=False)
    tx   = make_tx(inputs=[inp], outputs=[pay, chg])
    result = H.detect_change_output(tx)
    assert result.code == "PROBABLE_CHANGE"

def test_change_inference_no_trigger_mixed_inputs():
    i1  = make_utxo(script_type="p2wpkh", sats=60_000)
    i2  = make_utxo(script_type="p2tr",   sats=60_000)
    o1  = make_utxo(script_type="p2wpkh", sats=50_000, is_spent=False)
    o2  = make_utxo(script_type="p2tr",   sats=50_000, is_spent=False)
    tx  = make_tx(inputs=[i1, i2], outputs=[o1, o2])
    assert H.detect_change_output(tx) is None

def test_change_inference_no_trigger_single_output():
    tx = make_tx(
        inputs  = [make_utxo(script_type="p2wpkh")],
        outputs = [make_utxo(script_type="p2wpkh", is_spent=False)],
    )
    assert H.detect_change_output(tx) is None


# ── SCRIPT TYPE MISMATCH ──────────────────────────────────────────────────────

def test_script_mismatch_triggers():
    inp = make_utxo(script_type="p2wpkh")
    out = make_utxo(script_type="p2tr", is_spent=False)
    tx  = make_tx(inputs=[inp], outputs=[out])
    assert H.detect_script_mismatch(tx).code == "SCRIPT_TYPE_MISMATCH"

def test_script_mismatch_no_trigger():
    inp = make_utxo(script_type="p2wpkh")
    out = make_utxo(script_type="p2wpkh", is_spent=False)
    tx  = make_tx(inputs=[inp], outputs=[out])
    assert H.detect_script_mismatch(tx) is None


# ── CONSOLIDATION ─────────────────────────────────────────────────────────────

def test_consolidation_triggers():
    inputs = [make_utxo(sats=30_000) for _ in range(4)]
    output = [make_utxo(sats=118_000, is_spent=False)]
    tx = make_tx(inputs=inputs, outputs=output)
    assert H.detect_consolidation(tx).code == "CONSOLIDATION"

def test_consolidation_no_trigger_two_inputs():
    inputs = [make_utxo(sats=50_000), make_utxo(sats=50_000)]
    output = [make_utxo(sats=99_000, is_spent=False)]
    tx = make_tx(inputs=inputs, outputs=output)
    assert H.detect_consolidation(tx) is None


# ── UIOH ─────────────────────────────────────────────────────────────────────

def test_uioh_triggers():
    # largest input (90k) alone covers outputs (50k) + 2x fee (2k) = 52k
    inputs  = [make_utxo(sats=90_000), make_utxo(sats=20_000)]
    outputs = [make_utxo(sats=50_000, is_spent=False)]
    tx = make_tx(inputs=inputs, outputs=outputs, fee_sats=1_000)
    assert H.detect_uioh(tx).code == "UIOH"

def test_uioh_no_trigger_when_all_inputs_needed():
    # each input is necessary: 40k + 40k needed for 78k output
    inputs  = [make_utxo(sats=40_000), make_utxo(sats=40_000)]
    outputs = [make_utxo(sats=78_000, is_spent=False)]
    tx = make_tx(inputs=inputs, outputs=outputs, fee_sats=1_000)
    assert H.detect_uioh(tx) is None

def test_uioh_no_trigger_single_input():
    tx = make_tx()
    assert H.detect_uioh(tx) is None


# ── ENGINE ────────────────────────────────────────────────────────────────────

def test_engine_runs_all_detectors():
    engine = FingerprintEngine()
    # tx that triggers rbf + consolidation
    inputs = [make_utxo(sats=30_000) for _ in range(4)]
    output = [make_utxo(sats=118_000, is_spent=False)]
    tx = make_tx(inputs=inputs, outputs=output, is_rbf=True)
    results = engine.annotate(tx)
    codes = {r.code for r in results}
    assert "RBF_SIGNALING" in codes
    assert "CONSOLIDATION" in codes

def test_engine_respects_enabled_list():
    engine = FingerprintEngine(enabled=["rbf"])
    tx = make_tx(is_rbf=True, locktime=850_000, locktime_type="block_height")
    results = engine.annotate(tx)
    codes = {r.code for r in results}
    assert "RBF_SIGNALING" in codes
    assert "ANTI_FEE_SNIPING" not in codes  # not in enabled list

def test_engine_annotate_inplace():
    engine = FingerprintEngine()
    tx = make_tx(is_rbf=True)
    engine.annotate_inplace(tx)
    assert any(a.code == "RBF_SIGNALING" for a in tx.annotations)

def test_engine_empty_result_for_clean_tx():
    engine = FingerprintEngine()
    # plain tx — nothing suspicious
    tx = make_tx(
        inputs  = [make_utxo(sats=100_000, address="bc1qin",  script_type="p2wpkh")],
        outputs = [make_utxo(sats=99_000,  address="bc1qout", script_type="p2wpkh",
                             is_spent=False)],
        is_rbf=False, locktime=0, locktime_type="none", fee_sats=1_000,
    )
    # only possible trigger: round_payment (99_000 not round), change_inference
    results = engine.annotate(tx)
    codes   = {r.code for r in results}
    # should not have privacy-critical flags
    assert "ADDRESS_REUSE"   not in codes
    assert "UIOH"            not in codes
    assert "RBF_SIGNALING"   not in codes
