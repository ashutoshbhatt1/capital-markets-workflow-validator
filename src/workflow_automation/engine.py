from __future__ import annotations

from collections.abc import Iterable

from .adapters import DryRunApiAdapter
from .controls import ApprovalQueue
from .feeds import EventNormalizer, JsonLineEventFeed
from .models import Decision, DecisionType, NormalizedEvent, WorkflowContext
from .monitoring import AuditLog
from .rules import ThresholdRule


class WorkflowEngine:
    def __init__(
        self,
        rules: Iterable[ThresholdRule],
        context: WorkflowContext,
        api_adapter: DryRunApiAdapter,
        approval_queue: ApprovalQueue,
        audit_log: AuditLog,
    ) -> None:
        self.rules = list(rules)
        self.context = context
        self.normalizer = EventNormalizer()
        self.api_adapter = api_adapter
        self.approval_queue = approval_queue
        self.audit_log = audit_log

    def process_json_lines(self, lines: Iterable[str]) -> list[Decision]:
        decisions: list[Decision] = []
        for event in JsonLineEventFeed(lines).events():
            normalized = self.normalizer.normalize(event)
            self.audit_log.record_event(normalized)
            decisions.extend(self.process_event(normalized))
        return decisions

    def process_event(self, event: NormalizedEvent) -> list[Decision]:
        decisions: list[Decision] = []
        for rule in self.rules:
            decision = rule.evaluate(event, self.context)
            if decision is None:
                continue
            decisions.append(decision)
            self.audit_log.record_decision(decision)
            if decision.decision_type is DecisionType.APPROVE:
                self.audit_log.record_api_result(self.api_adapter.submit(decision))
            elif decision.decision_type is DecisionType.REVIEW:
                self.approval_queue.submit(decision)
        return decisions

    def approve_pending(self, decision_id: str) -> None:
        decision = self.approval_queue.approve(decision_id)
        self.audit_log.record_api_result(self.api_adapter.submit(decision))
