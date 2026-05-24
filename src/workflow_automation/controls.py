from __future__ import annotations

from dataclasses import dataclass, field

from .models import Decision, DecisionType


@dataclass
class ApprovalQueue:
    pending: dict[str, Decision] = field(default_factory=dict)
    approved: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)

    def submit(self, decision: Decision) -> None:
        if decision.decision_type is DecisionType.REVIEW:
            self.pending[decision.decision_id] = decision

    def approve(self, decision_id: str) -> Decision:
        decision = self.pending.pop(decision_id)
        self.approved.append(decision_id)
        return decision

    def reject(self, decision_id: str) -> Decision:
        decision = self.pending.pop(decision_id)
        self.rejected.append(decision_id)
        return decision


class SafetyGate:
    def __init__(self, execution_enabled: bool = False) -> None:
        self.execution_enabled = execution_enabled

    def can_execute(self) -> bool:
        return self.execution_enabled
