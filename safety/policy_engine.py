"""Motor de políticas: aplica regras de negócio e compliance."""
from dataclasses import dataclass, field
from typing import List, Callable, Any


@dataclass
class Policy:
    name: str
    description: str
    check: Callable[[Any], bool]
    severity: str = "warn"  # warn | block
    enabled: bool = True


class PolicyEngine:
    def __init__(self):
        self._policies: List[Policy] = []
        self._register_defaults()

    def _register_defaults(self):
        self.add(Policy(
            name="max_input_length",
            description="Input não pode exceder 4000 tokens (aprox)",
            check=lambda x: len(str(x)) <= 16000,
            severity="block",
        ))
        self.add(Policy(
            name="no_empty_input",
            description="Input não pode ser vazio",
            check=lambda x: bool(str(x).strip()),
            severity="block",
        ))

    def add(self, policy: Policy):
        self._policies.append(policy)

    def evaluate(self, data: Any) -> dict:
        violations = []
        blocked = False
        for p in self._policies:
            if not p.enabled:
                continue
            try:
                passed = p.check(data)
            except Exception as e:
                passed = False
            if not passed:
                violations.append({"policy": p.name, "severity": p.severity, "description": p.description})
                if p.severity == "block":
                    blocked = True
        return {
            "ok": not blocked,
            "blocked": blocked,
            "violations": violations,
            "violation_count": len(violations),
        }
