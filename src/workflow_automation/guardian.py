from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from .models import Decision


Severity = Literal["info", "caution", "high"]


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    label: str
    detail: str


@dataclass(frozen=True)
class RecommendedTest:
    name: str
    purpose: str
    expected_outcome: str


@dataclass(frozen=True)
class IncidentBrief:
    headline: str
    severity: Severity
    summary: str
    violated_controls: list[str]
    evidence: list[EvidenceReference]
    uncertainties: list[str]
    recommended_tests: list[RecommendedTest]
    human_action: str
    execution_authorized: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_guardian_bundle(
    scenario_id: str,
    scenario_name: str,
    scenario_context: str,
    decisions: list[Decision],
    audit_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Create the only payload the AI boundary is allowed to inspect."""

    return {
        "scenario": {
            "id": scenario_id,
            "name": scenario_name,
            "context": scenario_context,
            "mode": "sanitized_replay",
        },
        "control_policy": {
            "execution_enabled": False,
            "manual_review_required": True,
            "ai_role": "explain_and_recommend_tests_only",
            "prohibited_ai_actions": [
                "approve a workflow",
                "change a configured limit",
                "submit an API action",
                "place or route an order",
            ],
        },
        "decisions": [
            {
                "decision_id": decision.decision_id,
                "event_id": decision.event_id,
                "decision_type": decision.decision_type.value,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "payload": decision.payload,
            }
            for decision in decisions
        ],
        "audit_snapshot": audit_snapshot,
    }


def replay_brief(bundle: dict[str, Any]) -> IncidentBrief:
    """Deterministic fixture used when a live OpenAI key is not configured."""

    scenario_id = str(bundle["scenario"]["id"])
    decisions = bundle.get("decisions", [])
    primary = decisions[-1] if decisions else {}
    event_id = str(primary.get("event_id") or "no-event")
    decision_id = str(primary.get("decision_id") or "no-decision")

    fixtures: dict[str, IncidentBrief] = {
        "limit-breach": IncidentBrief(
            headline="Hard limit breach correctly stopped the workflow",
            severity="high",
            summary=(
                "The deterministic validator rejected the event because its value exceeded the "
                "configured safety ceiling. Keep the rejection in place and investigate the source value."
            ),
            violated_controls=["Configured maximum value"],
            evidence=[
                EvidenceReference(event_id, "Source event", "Reported value 105.0 against a maximum of 100.0."),
                EvidenceReference(decision_id, "Validator decision", "The deterministic outcome is reject."),
            ],
            uncertainties=["The replay does not identify whether the source spike was valid or malformed."],
            recommended_tests=[
                RecommendedTest(
                    "test_limit_boundary_values",
                    "Exercise values immediately below, at, and above the maximum.",
                    "Only values above the configured maximum are rejected.",
                )
            ],
            human_action="Review the source event and limit configuration; do not override the rejection from this report.",
        ),
        "approval-drift": IncidentBrief(
            headline="Manual approval remains the controlling gate",
            severity="caution",
            summary=(
                "The event passed the quality threshold, but the replay policy requires human approval. "
                "No downstream submission occurred."
            ),
            violated_controls=[],
            evidence=[
                EvidenceReference(event_id, "Source event", "Quality score 85.0 passed the 80.0 threshold."),
                EvidenceReference(decision_id, "Validator decision", "The outcome is review, not approve."),
            ],
            uncertainties=["The replay contains no reviewer identity or approval rationale."],
            recommended_tests=[
                RecommendedTest(
                    "test_manual_gate_survives_replay",
                    "Verify review decisions cannot submit through the dry-run adapter.",
                    "API result count remains zero until a human review action occurs.",
                )
            ],
            human_action="Confirm the evidence and record an explicit human decision outside the AI report.",
        ),
        "thin-evidence": IncidentBrief(
            headline="Near-threshold evidence is too weak for automatic action",
            severity="caution",
            summary=(
                "The event sits inside the review band rather than clearly passing the threshold. "
                "The safest result is to preserve review status and collect another observation."
            ),
            violated_controls=[],
            evidence=[
                EvidenceReference(event_id, "Source event", "Quality score 45.0 falls inside the configured review band."),
                EvidenceReference(decision_id, "Validator decision", "The deterministic outcome is review."),
            ],
            uncertainties=["One event is insufficient to establish whether the low score is persistent."],
            recommended_tests=[
                RecommendedTest(
                    "test_review_band_edges",
                    "Cover both edges of the configured review band.",
                    "Near-threshold events consistently route to human review.",
                )
            ],
            human_action="Collect corroborating evidence before changing the workflow state.",
        ),
    }
    return fixtures.get(
        scenario_id,
        IncidentBrief(
            headline="Replay requires human review",
            severity="info",
            summary="The sanitized replay was processed, but no scenario-specific fixture is available.",
            violated_controls=[],
            evidence=[EvidenceReference(event_id, "Replay event", "A deterministic event was processed.")],
            uncertainties=["No scenario-specific analysis is available."],
            recommended_tests=[],
            human_action="Inspect the deterministic audit record.",
        ),
    )
