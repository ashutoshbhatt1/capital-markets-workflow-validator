from __future__ import annotations

import json
from io import BytesIO

import pytest

from workflow_automation.ai_explainer import (
    DEFAULT_MODEL,
    GuardianAIError,
    OpenAIResponsesExplainer,
)
from workflow_automation.guardian import build_guardian_bundle, replay_brief
from workflow_automation.models import Decision, DecisionType


def sample_bundle() -> dict[str, object]:
    decision = Decision(
        decision_id="decision-evt-limit-105",
        event_id="evt-limit-105",
        decision_type=DecisionType.REJECT,
        confidence=0.99,
        reason="Value exceeded configured safety limit.",
        payload={"entity": "DESK-A", "metric": "quality_score", "value": 105.0},
    )
    return build_guardian_bundle(
        "limit-breach",
        "Hard limit breach",
        "A sanitized source event exceeds the configured workflow ceiling.",
        [decision],
        {"counts": {"events": 1, "decisions": 1, "api_results": 0}},
    )


def test_bundle_hard_codes_read_only_ai_boundary() -> None:
    bundle = sample_bundle()

    assert bundle["control_policy"]["execution_enabled"] is False
    assert bundle["control_policy"]["ai_role"] == "explain_and_recommend_tests_only"
    assert bundle["decisions"][0]["decision_type"] == "reject"


def test_replay_brief_never_authorizes_execution() -> None:
    brief = replay_brief(sample_bundle())

    assert brief.severity == "high"
    assert brief.execution_authorized is False
    assert brief.evidence[0].evidence_id == "evt-limit-105"


def test_live_explainer_requires_an_api_key() -> None:
    with pytest.raises(GuardianAIError, match="OPENAI_API_KEY"):
        OpenAIResponsesExplainer(api_key="").explain(sample_bundle())


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.body = BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body.read()


def test_live_explainer_uses_sol_responses_and_strict_schema() -> None:
    captured: dict[str, object] = {}
    incident = {
        "headline": "Limit stopped",
        "severity": "high",
        "summary": "The deterministic limit rejected the event.",
        "violated_controls": ["Configured maximum value"],
        "evidence": [
            {"evidence_id": "evt-limit-105", "label": "Source event", "detail": "Value 105.0."}
        ],
        "uncertainties": ["Source validity is unknown."],
        "recommended_tests": [
            {
                "name": "test_limit_boundary_values",
                "purpose": "Cover the boundary.",
                "expected_outcome": "Values above 100 are rejected.",
            }
        ],
        "human_action": "Review the source event.",
        "execution_authorized": False,
    }

    def opener(request: object, timeout: int) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": json.dumps(incident)}],
                    }
                ]
            }
        )

    brief = OpenAIResponsesExplainer(api_key="test-key", opener=opener).explain(sample_bundle())
    request = captured["request"]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload["model"] == DEFAULT_MODEL
    assert payload["reasoning"] == {"effort": "medium"}
    assert payload["store"] is False
    assert payload["text"]["format"]["strict"] is True
    assert "tools" not in payload
    assert brief.execution_authorized is False
