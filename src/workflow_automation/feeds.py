from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from typing import Any

from .models import Event, NormalizedEvent


class JsonLineEventFeed:
    def __init__(self, lines: Iterable[str]) -> None:
        self.lines = lines

    def events(self) -> Iterator[Event]:
        for line in self.lines:
            if not line.strip():
                continue
            row = json.loads(line)
            yield Event(
                event_id=str(row["event_id"]),
                source=str(row.get("source", "unknown")),
                timestamp=parse_timestamp(row["timestamp"]),
                payload=dict(row.get("payload", {})),
            )


class EventNormalizer:
    def normalize(self, event: Event) -> NormalizedEvent:
        payload = event.payload
        return NormalizedEvent(
            event_id=event.event_id,
            source=event.source,
            timestamp=event.timestamp,
            entity=str(payload["entity"]),
            metric=str(payload["metric"]),
            value=float(payload["value"]),
            attributes=dict(payload.get("attributes", {})),
        )


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
