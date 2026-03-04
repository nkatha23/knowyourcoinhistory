# Fingerprinting Heuristics

KYCC runs eight privacy-analysis detectors on every transaction. Each produces zero or more `Annotation` objects attached to the `TxNode`. Annotations are shown as coloured dots on the transaction card in the graph and as expandable rows in the right panel.

Severity levels:
- `info` (blue) — observable pattern, low privacy risk
- `warning` (amber) — moderate risk, context-dependent
- `flag` (red) — high-confidence privacy leak

---

## Heuristic Reference

### 1. UIOH — Unnecessary Input Ownership Heuristic

**Code:** `UIOH`
**Severity:** `warning`
**Config key:** `uioh`

Fires when the transaction has more than one input **and** the total input value exceeds the total output value by more than the fee. This suggests at least one input was unnecessary to fund the outputs, revealing that the sender controls multiple UTXOs and chose to include extras (possibly for UTXO consolidation or to meet a minimum threshold).

### 2. Address Reuse

**Code:** `ADDRESS_REUSE`
**Severity:** `flag`
**Config key:** `address_reuse`

Fires when an address appears in both the inputs and the outputs of the same transaction, or when an input address matches a previously labeled address in the label store. Address reuse directly links sender and receiver identities.

### 3. Round Payment

**Code:** `ROUND_PAYMENT`
**Severity:** `info`
**Config key:** `round_payment`

Fires when one or more output values are round numbers in BTC (e.g. 0.001, 0.01, 0.1, 1.0) or round numbers in satoshis (multiples of 10,000, 100,000, 1,000,000). Round amounts are a strong signal that a value is a payment rather than change, reducing ambiguity between outputs.

### 4. Change Inference

**Code:** `PROBABLE_CHANGE`
**Severity:** `info`
**Config key:** `change_inference`

Identifies the most likely change output using a combination of:
- Script type match — change output has the same script type as the input(s)
- Value heuristic — the smaller of two outputs when one is round is likely change
- Dust threshold — outputs below 546 sats are unlikely to be intentional payments

### 5. Script Type Mismatch

**Code:** `SCRIPT_TYPE_MISMATCH`
**Severity:** `warning`
**Config key:** `script_mismatch`

Fires when inputs and outputs use different script types (e.g. P2WPKH inputs sending to a P2PKH output). Modern wallets produce homogeneous transactions; mismatches often indicate cross-wallet transactions or deliberately mixed script types.

### 6. RBF Signaling

**Code:** `RBF_SIGNALING`
**Severity:** `info`
**Config key:** `rbf`

Fires when any input has `nSequence ≤ 0xFFFFFFFD`, which opts the transaction into Replace-By-Fee. While not a privacy concern on its own, RBF signaling is a wallet fingerprint and can indicate the wallet software in use.

### 7. Locktime Pattern

**Codes:** `ANTI_FEE_SNIPING` (severity `info`), `TIMELOCK_UNIX` (severity `info`)
**Config key:** `locktime`

- `ANTI_FEE_SNIPING` — locktime is a recent block height (within ~10 blocks of the chain tip), a technique used by Bitcoin Core and compatible wallets to discourage fee sniping. Reveals the wallet software.
- `TIMELOCK_UNIX` — locktime is a Unix timestamp (> 500,000,000), indicating a time-locked transaction.

### 8. Consolidation

**Code:** `CONSOLIDATION`
**Severity:** `info`
**Config key:** `consolidation`

Fires when the transaction has 3 or more inputs and 1–2 outputs. This is the signature of a UTXO consolidation sweep, which links all input addresses to a single controlling entity and is common during periods of low fees.

---

## Disabling Heuristics

Individual heuristics can be disabled in `kycc.toml`:

```toml
[fingerprint]
enabled    = true
heuristics = ["uioh", "address_reuse", "round_payment", "change_inference",
               "script_mismatch", "rbf", "locktime", "consolidation"]
```

Remove any key from the list to disable it globally. Individual heuristics can also be toggled per-session in the Settings modal without restarting the server.

---

## Annotation to Config Key Map

| Annotation code | Config key |
|-----------------|-----------|
| `UIOH` | `uioh` |
| `ADDRESS_REUSE` | `address_reuse` |
| `ROUND_PAYMENT` | `round_payment` |
| `PROBABLE_CHANGE` | `change_inference` |
| `SCRIPT_TYPE_MISMATCH` | `script_mismatch` |
| `RBF_SIGNALING` | `rbf` |
| `ANTI_FEE_SNIPING` | `locktime` |
| `TIMELOCK_UNIX` | `locktime` |
| `CONSOLIDATION` | `consolidation` |
