export type Severity = "info" | "caution" | "high";

export type Evidence = {
  evidence_id: string;
  label: string;
  detail: string;
};

export type RecommendedTest = {
  name: string;
  purpose: string;
  expected_outcome: string;
};

export type IncidentBrief = {
  headline: string;
  severity: Severity;
  summary: string;
  violated_controls: string[];
  evidence: Evidence[];
  uncertainties: string[];
  recommended_tests: RecommendedTest[];
  human_action: string;
  execution_authorized: false;
};

export type Scenario = {
  id: string;
  eyebrow: string;
  name: string;
  context: string;
  eventId: string;
  decisionId: string;
  value: number;
  threshold: number;
  maximum: number;
  decision: "REVIEW" | "REJECT";
  decisionReason: string;
  time: string;
  brief: IncidentBrief;
};

export const scenarios: Scenario[] = [
  {
    id: "limit-breach",
    eyebrow: "Scenario 01",
    name: "Hard limit breach",
    context: "A source event exceeds the configured workflow ceiling.",
    eventId: "evt-limit-105",
    decisionId: "decision-evt-limit-105",
    value: 105,
    threshold: 80,
    maximum: 100,
    decision: "REJECT",
    decisionReason: "Value exceeded configured safety limit.",
    time: "14:30:00 UTC",
    brief: {
      headline: "Hard limit breach correctly stopped the workflow",
      severity: "high",
      summary:
        "The deterministic validator rejected the event because its value exceeded the configured safety ceiling. Keep the rejection in place and investigate the source value.",
      violated_controls: ["Configured maximum value"],
      evidence: [
        {
          evidence_id: "evt-limit-105",
          label: "Source event",
          detail: "Reported value 105.0 against a maximum of 100.0.",
        },
        {
          evidence_id: "decision-evt-limit-105",
          label: "Validator decision",
          detail: "The deterministic outcome is reject.",
        },
      ],
      uncertainties: [
        "The replay does not identify whether the source spike was valid or malformed.",
      ],
      recommended_tests: [
        {
          name: "test_limit_boundary_values",
          purpose: "Exercise values immediately below, at, and above the maximum.",
          expected_outcome: "Only values above the configured maximum are rejected.",
        },
      ],
      human_action:
        "Review the source event and limit configuration; do not override the rejection from this report.",
      execution_authorized: false,
    },
  },
  {
    id: "approval-drift",
    eyebrow: "Scenario 02",
    name: "Manual approval drift",
    context: "A passing score must remain queued for explicit human review.",
    eventId: "evt-review-085",
    decisionId: "decision-evt-review-085",
    value: 85,
    threshold: 80,
    maximum: 100,
    decision: "REVIEW",
    decisionReason: "Metric passed threshold; manual approval remains required.",
    time: "14:31:00 UTC",
    brief: {
      headline: "Manual approval remains the controlling gate",
      severity: "caution",
      summary:
        "The event passed the quality threshold, but replay policy requires human approval. No downstream submission occurred.",
      violated_controls: [],
      evidence: [
        {
          evidence_id: "evt-review-085",
          label: "Source event",
          detail: "Quality score 85.0 passed the 80.0 threshold.",
        },
        {
          evidence_id: "decision-evt-review-085",
          label: "Validator decision",
          detail: "The outcome is review, not approve.",
        },
      ],
      uncertainties: ["The replay contains no reviewer identity or approval rationale."],
      recommended_tests: [
        {
          name: "test_manual_gate_survives_replay",
          purpose: "Verify review decisions cannot submit through the dry-run adapter.",
          expected_outcome: "API result count remains zero until a human review action occurs.",
        },
      ],
      human_action: "Confirm the evidence and record an explicit human decision outside the AI report.",
      execution_authorized: false,
    },
  },
  {
    id: "thin-evidence",
    eyebrow: "Scenario 03",
    name: "Thin evidence",
    context: "A near-threshold event needs more evidence before any state change.",
    eventId: "evt-thin-045",
    decisionId: "decision-evt-thin-045",
    value: 45,
    threshold: 80,
    maximum: 100,
    decision: "REVIEW",
    decisionReason: "Metric is near threshold and requires review.",
    time: "14:32:00 UTC",
    brief: {
      headline: "Near-threshold evidence is too weak for automatic action",
      severity: "caution",
      summary:
        "The event sits inside the review band rather than clearly passing the threshold. Preserve review status and collect another observation.",
      violated_controls: [],
      evidence: [
        {
          evidence_id: "evt-thin-045",
          label: "Source event",
          detail: "Quality score 45.0 falls inside the configured review band.",
        },
        {
          evidence_id: "decision-evt-thin-045",
          label: "Validator decision",
          detail: "The deterministic outcome is review.",
        },
      ],
      uncertainties: ["One event is insufficient to establish whether the low score is persistent."],
      recommended_tests: [
        {
          name: "test_review_band_edges",
          purpose: "Cover both edges of the configured review band.",
          expected_outcome: "Near-threshold events consistently route to human review.",
        },
      ],
      human_action: "Collect corroborating evidence before changing the workflow state.",
      execution_authorized: false,
    },
  },
];

export const scenarioById = Object.fromEntries(
  scenarios.map((scenario) => [scenario.id, scenario]),
) as Record<string, Scenario>;
