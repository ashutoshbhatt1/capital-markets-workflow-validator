from __future__ import annotations

from dataclasses import dataclass

from .models import Decision, DecisionType, NormalizedEvent, WorkflowContext


@dataclass(frozen=True)
class ThresholdRule:
    metric: str
    threshold: float
    review_band: float = 0.1

    def evaluate(self, event: NormalizedEvent, context: WorkflowContext) -> Decision | None:
        if event.metric != self.metric:
            return None

        ratio = event.value / max(self.threshold, 1.0)
        confidence = min(0.99, max(0.0, ratio))
        decision_id = f"decision-{event.event_id}"

        if event.value > context.max_value:
            return Decision(
                decision_id=decision_id,
                event_id=event.event_id,
                decision_type=DecisionType.REJECT,
                confidence=confidence,
                reason="Value exceeded configured safety limit.",
                payload={"entity": event.entity, "metric": event.metric, "value": event.value},
            )

        if confidence >= context.min_confidence:
            decision_type = DecisionType.REVIEW if context.require_manual_approval else DecisionType.APPROVE
            return Decision(
                decision_id=decision_id,
                event_id=event.event_id,
                decision_type=decision_type,
                confidence=confidence,
                reason="Metric passed configured threshold.",
                payload={"entity": event.entity, "metric": event.metric, "value": event.value},
            )

        if confidence >= context.min_confidence - self.review_band:
            return Decision(
                decision_id=decision_id,
                event_id=event.event_id,
                decision_type=DecisionType.REVIEW,
                confidence=confidence,
                reason="Metric is near threshold and requires review.",
                payload={"entity": event.entity, "metric": event.metric, "value": event.value},
            )

        return None
