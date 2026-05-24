from __future__ import annotations

from workflow_automation.adapters import DryRunApiAdapter
from workflow_automation.controls import SafetyGate
from workflow_automation.models import Decision, DecisionType


def decision() -> Decision:
    return Decision(
        decision_id="decision-evt-001",
        event_id="evt-001",
        decision_type=DecisionType.APPROVE,
        confidence=0.88,
        reason="test",
        payload={"entity": "ABC"},
    )


def test_adapter_builds_payload_without_submitting_when_gate_is_disabled() -> None:
    adapter = DryRunApiAdapter("/api/workflow/execute", SafetyGate(execution_enabled=False))

    result = adapter.submit(decision())

    assert result.submitted is False
    assert result.message == "dry_run_only"
    assert result.payload["decision_id"] == "decision-evt-001"


def test_adapter_marks_submission_when_gate_is_enabled() -> None:
    adapter = DryRunApiAdapter("/api/workflow/execute", SafetyGate(execution_enabled=True))

    result = adapter.submit(decision())

    assert result.submitted is True
    assert result.message == "submitted"
