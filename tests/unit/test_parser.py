from kycc.graph.parser import parse_tx
from kycc.script_utils import locktime_type


# ── minimal raw tx factory ────────────────────────────────────────────────────

def make_raw(
    sequence=0xFFFFFFFF,
    locktime=0,
    in_value=0.001,
    out_value=0.0009,
    in_spk="0014" + "a" * 40,
    out_spk="0014" + "b" * 40,
):
    return {
        "txid":     "a" * 64,
        "version":  2,
        "locktime": locktime,
        "size":     141,
        "weight":   564,
        "vin": [{
            "txid":     "b" * 64,
            "vout":     0,
            "sequence": sequence,
            "prevout": {
                "value": in_value,
                "scriptPubKey": {"hex": in_spk, "address": "bc1qinput"},
            },
        }],
        "vout": [{
            "n":    0,
            "value": out_value,
            "scriptPubKey": {"hex": out_spk, "address": "bc1qoutput"},
        }],
    }


# ── tests ─────────────────────────────────────────────────────────────────────

def test_parse_returns_txnode():
    node = parse_tx(make_raw())
    assert node.txid == "a" * 64
    assert len(node.inputs)  == 1
    assert len(node.outputs) == 1


def test_balance_invariant():
    node = parse_tx(make_raw(in_value=0.001, out_value=0.0009))
    in_total  = sum(u.value_sats for u in node.inputs)
    out_total = sum(u.value_sats for u in node.outputs)
    assert in_total == out_total + node.fee_sats


def test_fee_computed_correctly():
    node = parse_tx(make_raw(in_value=0.001, out_value=0.0009))
    assert node.fee_sats == 10_000


def test_rbf_true_when_sequence_signaling():
    node = parse_tx(make_raw(sequence=0xFFFFFFFD))
    assert node.is_rbf is True


def test_rbf_false_when_final_sequence():
    node = parse_tx(make_raw(sequence=0xFFFFFFFF))
    assert node.is_rbf is False


def test_locktime_none():
    node = parse_tx(make_raw(locktime=0))
    assert node.locktime_type == "none"


def test_locktime_block_height():
    node = parse_tx(make_raw(locktime=850_000))
    assert node.locktime_type == "block_height"


def test_locktime_unix_timestamp():
    node = parse_tx(make_raw(locktime=1_700_000_000))
    assert node.locktime_type == "unix_timestamp"


def test_script_type_p2wpkh_input():
    node = parse_tx(make_raw(in_spk="0014" + "a" * 40))
    assert node.inputs[0].script_type == "p2wpkh"


def test_script_type_p2tr_output():
    node = parse_tx(make_raw(out_spk="5120" + "a" * 64))
    assert node.outputs[0].script_type == "p2tr"


def test_script_type_op_return():
    node = parse_tx(make_raw(out_spk="6a" + "deadbeef"))
    assert node.outputs[0].script_type == "op_return"


def test_coinbase_tx():
    raw = {
        "txid": "c" * 64, "version": 1, "locktime": 0,
        "size": 100, "weight": 400,
        "vin":  [{"coinbase": "03abcdef", "sequence": 0xFFFFFFFF}],
        "vout": [{"n": 0, "value": 3.125,
                  "scriptPubKey": {"hex": "0014" + "a"*40, "address": "bc1q..."}}],
    }
    node = parse_tx(raw)
    assert node.is_coinbase is True
    assert node.fee_sats    is None
    assert node.inputs[0].script_type == "coinbase"


def test_value_sats_conversion():
    # 0.001 BTC == 100_000 sats exactly
    node = parse_tx(make_raw(in_value=0.001, out_value=0.0009))
    assert node.inputs[0].value_sats  == 100_000
    assert node.outputs[0].value_sats == 90_000
