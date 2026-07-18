from __future__ import annotations

import argparse
import json

from workflow_automation.adapters import DryRunApiAdapter
from workflow_automation.ai_explainer import GuardianAIError, OpenAIResponsesExplainer
from workflow_automation.controls import ApprovalQueue, SafetyGate
from workflow_automation.engine import WorkflowEngine
from workflow_automation.guardian import build_guardian_bundle, replay_brief
from workflow_automation.models import WorkflowContext
from workflow_automation.monitoring import AuditLog
from workflow_automation.rules import ThresholdRule


SCENARIOS = {
    "limit-breach": {
        "name": "Hard limit breach",
        "context": "A sanitized source event exceeds the configured workflow ceiling.",
        "line": '{"event_id":"evt-limit-105","source":"sanitized-replay","timestamp":"2026-07-17T14:30:00Z","payload":{"entity":"DESK-A","metric":"quality_score","value":105.0}}',
    },
    "approval-drift": {
        "name": "Manual approval drift",
        "context": "A passing score must remain queued for explicit human review.",
        "line": '{"event_id":"evt-review-085","source":"sanitized-replay","timestamp":"2026-07-17T14:31:00Z","payload":{"entity":"DESK-B","metric":"quality_score","value":85.0}}',
    },
    "thin-evidence": {
        "name": "Thin evidence",
        "context": "A near-threshold event needs more evidence before any state change.",
        "line": '{"event_id":"evt-thin-045","source":"sanitized-replay","timestamp":"2026-07-17T14:32:00Z","payload":{"entity":"DESK-C","metric":"quality_score","value":45.0}}',
    },
}


def run(scenario_id: str, live: bool) -> dict[str, object]:
    scenario = SCENARIOS[scenario_id]
    engine = WorkflowEngine(
        rules=[ThresholdRule(metric="quality_score", threshold=80.0)],
        context=WorkflowContext(
            environment="sanitized_replay",
            require_manual_approval=True,
            max_value=100.0,
            min_confidence=0.6,
        ),
        api_adapter=DryRunApiAdapter("/api/workflow/execute", SafetyGate(execution_enabled=False)),
        approval_queue=ApprovalQueue(),
        audit_log=AuditLog(),
    )
    decisions = engine.process_json_lines([scenario["line"]])
    bundle = build_guardian_bundle(
        scenario_id,
        scenario["name"],
        scenario["context"],
        decisions,
        engine.audit_log.snapshot(),
    )
    mode = "gpt-5.6-sol" if live else "replay-fixture"
    if live:
        try:
            brief = OpenAIResponsesExplainer().explain(bundle)
        except GuardianAIError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        brief = replay_brief(bundle)
    return {"mode": mode, "bundle": bundle, "brief": brief.to_dict()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FuturesPlaybook Guardian hackathon demo.")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="limit-breach")
    parser.add_argument("--live", action="store_true", help="Call GPT-5.6 Sol through the Responses API.")
    args = parser.parse_args()
    print(json.dumps(run(args.scenario, args.live), indent=2, default=str))
