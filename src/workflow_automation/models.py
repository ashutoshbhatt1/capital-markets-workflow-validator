from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DecisionType(str, Enum):
    APPROVE = "approve"
    REVIEW = "review"
    REJECT = "reject"


@dataclass(frozen=True)
class Event:
    event_id: str
    source: str
    timestamp: datetime
    payload: dict[str, Any]


@dataclass(frozen=True)
class NormalizedEvent:
    event_id: str
    source: str
    timestamp: datetime
    entity: str
    metric: str
    value: float
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowContext:
    environment: str = "replay"
    require_manual_approval: bool = True
    max_value: float = 100.0
    min_confidence: float = 0.6


@dataclass(frozen=True)
class Decision:
    decision_id: str
    event_id: str
    decision_type: DecisionType
    confidence: float
    reason: str
    payload: dict[str, Any] = field(default_factory=dict)
