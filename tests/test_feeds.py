from __future__ import annotations

from workflow_automation.feeds import EventNormalizer, JsonLineEventFeed


def test_json_line_feed_parses_and_normalizes_event() -> None:
    lines = [
        '{"event_id":"evt-001","source":"unit","timestamp":"2026-05-01T10:00:00Z","payload":{"entity":"ABC","metric":"quality_score","value":91.25}}'
    ]

    event = next(JsonLineEventFeed(lines).events())
    normalized = EventNormalizer().normalize(event)

    assert normalized.event_id == "evt-001"
    assert normalized.source == "unit"
    assert normalized.entity == "ABC"
    assert normalized.metric == "quality_score"
    assert normalized.value == 91.25
