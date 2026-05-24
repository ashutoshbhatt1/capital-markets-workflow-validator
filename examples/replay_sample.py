from __future__ import annotations

from workflow_automation.adapters import DryRunApiAdapter
from workflow_automation.controls import ApprovalQueue, SafetyGate
from workflow_automation.engine import WorkflowEngine
from workflow_automation.models import WorkflowContext
from workflow_automation.monitoring import AuditLog
from workflow_automation.rules import ThresholdRule


def sample_lines() -> list[str]:
    return [
        '{"event_id":"evt-001","source":"sample","timestamp":"2026-05-01T14:30:00Z","payload":{"entity":"ABC","metric":"quality_score","value":72.5}}',
        '{"event_id":"evt-002","source":"sample","timestamp":"2026-05-01T14:31:00Z","payload":{"entity":"XYZ","metric":"quality_score","value":105.0}}',
    ]


if __name__ == "__main__":
    engine = WorkflowEngine(
        rules=[ThresholdRule(metric="quality_score", threshold=80.0)],
        context=WorkflowContext(require_manual_approval=True, max_value=100.0),
        api_adapter=DryRunApiAdapter("/api/workflow/execute", SafetyGate(execution_enabled=False)),
        approval_queue=ApprovalQueue(),
        audit_log=AuditLog(),
    )
    decisions = engine.process_json_lines(sample_lines())
    print(f"events={engine.audit_log.snapshot()['counts']['events']} decisions={len(decisions)}")
    print(engine.audit_log.snapshot())
