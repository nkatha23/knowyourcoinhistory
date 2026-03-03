from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["info", "warning", "flag"]


@dataclass
class HeuristicResult:
    code:        str
    severity:    Severity
    description: str
    affected:    list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "code":        self.code,
            "severity":    self.severity,
            "description": self.description,
            "affected":    self.affected,
        }
