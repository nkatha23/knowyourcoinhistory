from kycc.graph.models import ScriptType

def classify_script(script_pubkey_hex: str) -> ScriptType:
    s = script_pubkey_hex.lower()

    if s == "" or s == "00":
        return "coinbase"
    if s.startswith("6a"):
        return "op_return"
    if s.startswith("0014") and len(s) == 44:
        return "p2wpkh"
    if s.startswith("0020") and len(s) == 68:
        return "p2wsh"
    if s.startswith("5120") and len(s) == 68:
        return "p2tr"
    if s.startswith("76a914") and s.endswith("88ac"):
        return "p2pkh"
    if s.startswith("a914") and s.endswith("87"):
        return "p2sh"

    return "unknown"


def is_rbf(vin: list[dict]) -> bool:
    """Any input with nSequence <= 0xFFFFFFFD signals RBF (BIP-125)."""
    return any(inp.get("sequence", 0xFFFFFFFF) <= 0xFFFFFFFD for inp in vin)


def locktime_type(locktime: int) -> str:
    if locktime == 0:
        return "none"
    if locktime < 500_000_000:
        return "block_height"
    return "unix_timestamp"