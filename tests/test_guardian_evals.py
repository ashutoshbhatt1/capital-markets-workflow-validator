import json
from pathlib import Path

from examples.run_guardian_demo import run


CASES = Path(__file__).parents[1] / "evals" / "guardian_cases.jsonl"


def test_guardian_replay_cases_match_published_expectations() -> None:
    for line in CASES.read_text().splitlines():
        case = json.loads(line)
        result = run(case["scenario_id"], live=False)
        brief = result["brief"]
        decisions = result["bundle"]["decisions"]
        evidence_ids = {item["evidence_id"] for item in brief["evidence"]}

        assert decisions[-1]["decision_type"] == case["expected_decision"]
        assert brief["severity"] == case["expected_severity"]
        assert set(case["required_evidence_ids"]) <= evidence_ids
        assert brief["execution_authorized"] is case["execution_authorized"] is False
