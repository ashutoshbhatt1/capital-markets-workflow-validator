from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .controls import SafetyGate
from .models import Decision


@dataclass(frozen=True)
class ApiResult:
    submitted: bool
    endpoint: str
    payload: dict[str, Any]
    message: str


class DryRunApiAdapter:
    def __init__(self, endpoint: str, safety_gate: SafetyGate) -> None:
        self.endpoint = endpoint
        self.safety_gate = safety_gate
        self.results: list[ApiResult] = []

    def submit(self, decision: Decision) -> ApiResult:
        payload = {
            "decision_id": decision.decision_id,
            "event_id": decision.event_id,
            "confidence": decision.confidence,
            "data": decision.payload,
        }
        result = ApiResult(
            submitted=self.safety_gate.can_execute(),
            endpoint=self.endpoint,
            payload=payload,
            message="submitted" if self.safety_gate.can_execute() else "dry_run_only",
        )
        self.results.append(result)
        return result
