# Hackathon submission kit

## One-line pitch

FuturesPlaybook Guardian uses GPT-5.6 Sol to turn deterministic workflow decisions into evidence-backed incident briefs—without giving AI permission to cross a single guardrail.

## Devpost description

Capital-markets operations produce plenty of logs but rarely a clear, immediate explanation of why a controlled workflow stopped. FuturesPlaybook Guardian adds a read-only intelligence layer to a deterministic validator. The validator evaluates sanitized replay events, applies limits and manual-approval policy, and emits an audit bundle. GPT-5.6 Sol then explains the outcome, cites only supplied evidence IDs, surfaces uncertainty, and recommends a concrete regression test.

The key design decision is separation of intelligence from authority. Sol cannot approve a workflow, change a threshold, call an execution tool, or route an order. Its strict structured output requires `execution_authorized: false`, and the application validates evidence references before displaying a report. Three replay scenarios make the behavior easy to judge without credentials: a hard limit breach, manual-approval drift, and thin evidence near a threshold.

## What is new for Build Week

- A GPT-5.6 Sol Responses API explainer with medium reasoning and strict structured output.
- An allowlisted, sanitized incident bundle rather than arbitrary prompts or raw operational data.
- Evidence-reference validation and an immutable false execution authorization.
- A polished control-room dashboard with three repeatable scenarios and offline judge mode.
- Safety evaluations, CI, and a public-ready demo path.

## Three-minute demo script

**0:00–0:25 — Problem.** Show the dashboard and explain that operators can see a reject but often spend too long reconstructing why. State the invariant: deterministic controls decide; AI only explains.

**0:25–1:15 — Hard limit breach.** Select “Hard limit breach,” run Guardian, and trace the event through the configured maximum to the reject decision. Point out the cited event and decision IDs, uncertainty, proposed boundary test, and `EXECUTION AUTHORIZED: FALSE`.

**1:15–1:55 — Approval drift.** Switch to “Manual approval drift.” Show that a passing score is still review—not approve—because policy requires a person. Highlight that no downstream submission occurred.

**1:55–2:25 — Thin evidence.** Switch to “Thin evidence.” Show how Sol communicates uncertainty and recommends collecting another observation instead of overstating confidence.

**2:25–2:50 — Architecture.** Briefly show the allowlisted bundle, strict schema, no-tools Responses call, and permanent dry-run safety gate in the repository.

**2:50–3:00 — Close.** “Guardian makes controlled systems easier to understand without making them easier to bypass.”

## Judge checklist

1. Open the deployed dashboard; no sign-in or key should be required for fixture mode.
2. Run all three scenario tabs and inspect the evidence and test recommendation.
3. Confirm every result shows execution authorization false.
4. Review `src/workflow_automation/ai_explainer.py` and `tests/test_guardian.py`.
5. Run `pytest -q` and `cd web && npm test`.

## Submission fields still requiring owner input

- Public demo URL after deployment approval.
- Public source URL after push approval.
- A short demo video URL.
- The required `/feedback` post URL after submitting product feedback to OpenAI.

## Feedback draft

The Responses API structured-output contract made it straightforward to keep the model inside a read-only incident-analysis role. The most useful improvement for this class of safety-sensitive developer tool would be a first-class dashboard that shows schema-validation failures and cited-input coverage for individual Responses calls. That would make it faster to evaluate whether a model explanation stayed grounded in the supplied audit bundle.
