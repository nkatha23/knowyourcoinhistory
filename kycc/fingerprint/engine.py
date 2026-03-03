"""
FingerprintEngine: runs configured heuristic detectors against a TxNode
and returns the list of HeuristicResult annotations.
"""
from typing import Callable, Optional
from kycc.graph.models import TxNode
from kycc.fingerprint.models import HeuristicResult
from kycc.fingerprint import heuristics as H

# Default detector registry — order matters for display
DEFAULT_DETECTORS: list[Callable[[TxNode], Optional[HeuristicResult]]] = [
    H.detect_rbf,
    H.detect_locktime,
    H.detect_address_reuse,
    H.detect_round_payment,
    H.detect_change_output,
    H.detect_script_mismatch,
    H.detect_consolidation,
    H.detect_uioh,
]

# Map config string → detector function
DETECTOR_MAP: dict[str, Callable[[TxNode], Optional[HeuristicResult]]] = {
    "rbf":              H.detect_rbf,
    "locktime":         H.detect_locktime,
    "address_reuse":    H.detect_address_reuse,
    "round_payment":    H.detect_round_payment,
    "change_inference": H.detect_change_output,
    "script_mismatch":  H.detect_script_mismatch,
    "consolidation":    H.detect_consolidation,
    "uioh":             H.detect_uioh,
}


class FingerprintEngine:
    def __init__(self, enabled: list[str] | None = None):
        """
        enabled: list of heuristic keys from kycc.toml [fingerprint].heuristics
                 If None, all detectors run.
        """
        if enabled is None:
            self._detectors = DEFAULT_DETECTORS
        else:
            self._detectors = [
                DETECTOR_MAP[k] for k in enabled if k in DETECTOR_MAP
            ]

    def annotate(self, tx: TxNode) -> list[HeuristicResult]:
        """Run all enabled detectors. Returns list of triggered results."""
        results = []
        for detector in self._detectors:
            result = detector(tx)
            if result is not None:
                results.append(result)
        return results

    def annotate_inplace(self, tx: TxNode) -> TxNode:
        """Annotate and attach results directly to tx.annotations."""
        from kycc.graph.models import HeuristicResult as GHR
        raw = self.annotate(tx)
        tx.annotations = [
            GHR(
                code        = r.code,
                severity    = r.severity,
                description = r.description,
                affected    = r.affected,
            )
            for r in raw
        ]
        return tx
