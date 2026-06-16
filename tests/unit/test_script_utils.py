from kycc.script_utils import classify_script, is_rbf, locktime_type


def test_classify_p2pkh_script():
    script = "76a914" + "ab" * 20 + "88ac"
    assert classify_script(script) == "p2pkh"


def test_classify_p2sh_script():
    script = "a914" + "cd" * 20 + "87"
    assert classify_script(script) == "p2sh"


def test_classify_p2wpkh_script():
    script = "0014" + "12" * 20
    assert classify_script(script) == "p2wpkh"


def test_classify_p2wsh_script():
    script = "0020" + "34" * 32
    assert classify_script(script) == "p2wsh"


def test_classify_p2tr_script():
    script = "5120" + "56" * 32
    assert classify_script(script) == "p2tr"


def test_classify_coinbase_empty_or_zero():
    assert classify_script("") == "coinbase"
    assert classify_script("00") == "coinbase"


def test_classify_op_return_script():
    assert classify_script("6a046b796363") == "op_return"


def test_classify_unknown_bare_script_types():
    assert classify_script("41" + "11" * 65 + "ac") == "unknown"
    assert classify_script("deadbeef") == "unknown"


def test_is_rbf_detects_signaling_sequence():
    assert is_rbf([{"sequence": 0xFFFFFFFF}, {"sequence": 0xFFFFFFFD}]) is True


def test_is_rbf_defaults_missing_sequence_to_final():
    assert is_rbf([{}, {"sequence": 0xFFFFFFFE}]) is False


def test_locktime_type():
    assert locktime_type(0) == "none"
    assert locktime_type(850_000) == "block_height"
    assert locktime_type(1_700_000_000) == "unix_timestamp"
