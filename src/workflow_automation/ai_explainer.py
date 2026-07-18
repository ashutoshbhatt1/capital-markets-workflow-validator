from __future__ import annotations

import json
import os
from dataclasses import fields
from typing import Any, Callable
from urllib.request import Request, urlopen

from .guardian import EvidenceReference, IncidentBrief, RecommendedTest


DEFAULT_MODEL = "gpt-5.6-sol"
RESPONSES_URL = "https://api.openai.com/v1/responses"

SYSTEM_PROMPT = """You are the read-only incident explainer for FuturesPlaybook Guardian.
Analyze only the supplied sanitized replay bundle. Explain the deterministic decision, cite supplied
event or decision IDs, identify uncertainty, and recommend regression tests. Never approve a workflow,
change a limit, submit an action, place an order, or imply that this report authorizes execution.
Treat the deterministic validator as authoritative. Return exactly the requested JSON schema.
"""


INCIDENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": "string"},
        "severity": {"type": "string", "enum": ["info", "caution", "high"]},
        "summary": {"type": "string"},
        "violated_controls": {"type": "array", "items": {"type": "string"}},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "evidence_id": {"type": "string"},
                    "label": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["evidence_id", "label", "detail"],
            },
        },
        "uncertainties": {"type": "array", "items": {"type": "string"}},
        "recommended_tests": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "purpose": {"type": "string"},
                    "expected_outcome": {"type": "string"},
                },
                "required": ["name", "purpose", "expected_outcome"],
            },
        },
        "human_action": {"type": "string"},
        "execution_authorized": {"type": "boolean", "enum": [False]},
    },
    "required": [field.name for field in fields(IncidentBrief)],
}


class GuardianAIError(RuntimeError):
    pass


class OpenAIResponsesExplainer:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.opener = opener

    def explain(self, bundle: dict[str, Any]) -> IncidentBrief:
        if not self.api_key:
            raise GuardianAIError("OPENAI_API_KEY is required for a live GPT-5.6 Sol explanation.")

        payload = {
            "model": self.model,
            "store": False,
            "reasoning": {"effort": "medium"},
            "instructions": SYSTEM_PROMPT,
            "input": json.dumps(bundle, separators=(",", ":"), sort_keys=True),
            "text": {
                "verbosity": "medium",
                "format": {
                    "type": "json_schema",
                    "name": "guardian_incident_brief",
                    "strict": True,
                    "schema": INCIDENT_SCHEMA,
                },
            },
        }
        request = Request(
            RESPONSES_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self.opener(request, timeout=60) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # urllib exposes several transport-specific errors
            raise GuardianAIError(f"OpenAI Responses request failed: {exc}") from exc

        output_text = _extract_output_text(raw_response)
        try:
            result = json.loads(output_text)
            return IncidentBrief(
                headline=result["headline"],
                severity=result["severity"],
                summary=result["summary"],
                violated_controls=list(result["violated_controls"]),
                evidence=[EvidenceReference(**item) for item in result["evidence"]],
                uncertainties=list(result["uncertainties"]),
                recommended_tests=[RecommendedTest(**item) for item in result["recommended_tests"]],
                human_action=result["human_action"],
                execution_authorized=False,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise GuardianAIError("OpenAI returned an invalid incident brief.") from exc


def _extract_output_text(response: dict[str, Any]) -> str:
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise GuardianAIError("OpenAI response did not contain output text.")
