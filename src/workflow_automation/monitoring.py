from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Any

from .adapters import ApiResult
from .models import Decision, NormalizedEvent


class AuditLog:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.api_results: list[dict[str, Any]] = []

    def record_event(self, event: NormalizedEvent) -> None:
        self.events.append(asdict(event))

    def record_decision(self, decision: Decision) -> None:
        self.decisions.append(asdict(decision))

    def record_api_result(self, result: ApiResult) -> None:
        self.api_results.append(asdict(result))

    def snapshot(self) -> dict[str, Any]:
        return {
            "counts": {
                "events": len(self.events),
                "decisions": len(self.decisions),
                "api_results": len(self.api_results),
            },
            "decision_types": Counter(row["decision_type"] for row in self.decisions),
            "latest_event": self.events[-1] if self.events else None,
            "latest_decision": self.decisions[-1] if self.decisions else None,
            "latest_api_result": self.api_results[-1] if self.api_results else None,
        }
