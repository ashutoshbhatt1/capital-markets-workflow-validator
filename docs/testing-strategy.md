# Testing Strategy

This project is a sanitized portfolio version of a capital-markets workflow validator. The goal is not to validate a trading strategy or profitability. The goal is to validate the backend workflow around an execution-style system before anything reaches downstream execution.

## What The Tests Cover

The pytest suite covers the workflow in layers:

1. Event ingestion
   - Reads JSONL input.
   - Parses timestamps consistently.
   - Converts raw payloads into typed backend models.

2. Rule evaluation
   - Validates approve, review, and reject outcomes.
   - Checks threshold behavior.
   - Confirms safety-limit rejections.

3. Approval controls
   - Routes review decisions into a manual approval queue.
   - Keeps pending decisions separate from approved or rejected decisions.

4. Dry-run API adapter behavior
   - Builds the outbound API payload.
   - Verifies the payload structure.
   - Blocks real submission when execution is disabled.

5. End-to-end replay
   - Replays a sample event through the full workflow.
   - Validates the path from JSONL input to normalized event, rule decision, approval gate, dry-run API result, audit log, and monitoring snapshot.

## Pre-Execution Automation

The key safety idea is that automation runs before execution is allowed.

In this repo, downstream execution is guarded by `SafetyGate`. When execution is disabled, the API adapter still builds and records the payload, but marks it as `dry_run_only` instead of submitted.

That means the workflow can be tested end to end without sending a real external request:

```text
event replay
  -> parser
  -> normalizer
  -> rules
  -> approval gate
  -> dry-run API payload
  -> audit log
  -> monitoring snapshot
```

Only when the safety gate is explicitly enabled does the adapter mark a result as submitted. The tests cover both paths:

- execution disabled: payload is created, submission is blocked
- execution enabled: payload is created, submission is allowed

## Why This Matters

In capital-markets systems, bad workflow behavior can be as risky as bad business logic. The data path, approval path, logging path, and outbound payload path all need to be validated before production execution is enabled.

This project demonstrates that approach in a simplified, public-safe way.

## How To Run

```bash
python -m pip install -e ".[dev]"
pytest
```
