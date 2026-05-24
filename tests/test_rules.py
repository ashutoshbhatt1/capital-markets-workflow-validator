from __future__ import annotations

from datetime import datetime, timezone

from workflow_automation.models import DecisionType, NormalizedEvent, WorkflowContext
from workflow_automation.rules import ThresholdRule


def event(value: float) -> NormalizedEvent:
    return NormalizedEvent(
        event_id="evt-001",
        source="unit",
        timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
        entity="ABC",
        metric="quality_score",
        value=value,
    )


def test_rule_requires_review_when_manual_approval_is_enabled() -> None:
    decision = ThresholdRule("quality_score", threshold=80).evaluate(
        event(90),
        WorkflowContext(require_manual_approval=True, min_confidence=0.6),
    )

    assert decision is not None
    assert decision.decision_type is DecisionType.REVIEW


def test_rule_rejects_when_value_exceeds_safety_limit() -> None:
    decision = ThresholdRule("quality_score", threshold=80).evaluate(
        event(125),
        WorkflowContext(max_value=100),
    )

    assert decision is not None
    assert decision.decision_type is DecisionType.REJECT


def test_rule_approves_when_manual_approval_is_disabled() -> None:
    decision = ThresholdRule("quality_score", threshold=80).evaluate(
        event(90),
        WorkflowContext(require_manual_approval=False, min_confidence=0.6),
    )

    assert decision is not None
    assert decision.decision_type is DecisionType.APPROVE
