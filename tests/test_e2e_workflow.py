from __future__ import annotations

from workflow_automation.adapters import DryRunApiAdapter
from workflow_automation.controls import ApprovalQueue, SafetyGate
from workflow_automation.engine import WorkflowEngine
from workflow_automation.models import DecisionType, WorkflowContext
from workflow_automation.monitoring import AuditLog
from workflow_automation.rules import ThresholdRule


def build_engine(require_manual_approval: bool = True, execution_enabled: bool = False) -> WorkflowEngine:
    return WorkflowEngine(
        rules=[ThresholdRule(metric="quality_score", threshold=80.0)],
        context=WorkflowContext(
            environment="replay",
            require_manual_approval=require_manual_approval,
            max_value=100.0,
            min_confidence=0.6,
        ),
        api_adapter=DryRunApiAdapter("/api/workflow/execute", SafetyGate(execution_enabled)),
        approval_queue=ApprovalQueue(),
        audit_log=AuditLog(),
    )


def test_e2e_replay_routes_review_decision_to_approval_queue() -> None:
    engine = build_engine(require_manual_approval=True)
    lines = [
        '{"event_id":"evt-001","source":"replay","timestamp":"2026-05-01T14:30:00Z","payload":{"entity":"ABC","metric":"quality_score","value":85.0}}'
    ]

    decisions = engine.process_json_lines(lines)
    snapshot = engine.audit_log.snapshot()

    assert len(decisions) == 1
    assert decisions[0].decision_type is DecisionType.REVIEW
    assert list(engine.approval_queue.pending) == ["decision-evt-001"]
    assert snapshot["counts"]["events"] == 1
    assert snapshot["counts"]["decisions"] == 1
    assert snapshot["counts"]["api_results"] == 0


def test_e2e_manual_approval_creates_dry_run_api_payload() -> None:
    engine = build_engine(require_manual_approval=True, execution_enabled=False)
    lines = [
        '{"event_id":"evt-001","source":"replay","timestamp":"2026-05-01T14:30:00Z","payload":{"entity":"ABC","metric":"quality_score","value":85.0}}'
    ]

    engine.process_json_lines(lines)
    engine.approve_pending("decision-evt-001")
    snapshot = engine.audit_log.snapshot()

    assert snapshot["counts"]["api_results"] == 1
    assert snapshot["latest_api_result"]["submitted"] is False
    assert snapshot["latest_api_result"]["message"] == "dry_run_only"


def test_e2e_auto_approval_executes_when_safety_gate_is_enabled() -> None:
    engine = build_engine(require_manual_approval=False, execution_enabled=True)
    lines = [
        '{"event_id":"evt-001","source":"replay","timestamp":"2026-05-01T14:30:00Z","payload":{"entity":"ABC","metric":"quality_score","value":85.0}}'
    ]

    decisions = engine.process_json_lines(lines)
    snapshot = engine.audit_log.snapshot()

    assert decisions[0].decision_type is DecisionType.APPROVE
    assert snapshot["latest_api_result"]["submitted"] is True
    assert snapshot["latest_api_result"]["payload"]["event_id"] == "evt-001"
