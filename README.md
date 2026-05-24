# Capital Markets Workflow Validator

Sanitized portfolio project demonstrating an end-to-end Python backend automation and validation workflow inspired by futures-market systems.

This repository intentionally abstracts strategy logic and sensitive implementation details. The focus is on capital-markets-style backend system design, test automation, JSON data validation, approval workflows, dry-run API execution, audit logging, and replay-based E2E testing.

## What It Demonstrates

- Python backend workflow orchestration
- Event-driven JSON/JSONL ingestion and normalization
- Configurable rule evaluation
- Risk-style safety limits and manual approval gates
- Dry-run REST API adapter pattern
- Audit logging and monitoring snapshots
- Pytest-based functional and integration testing
- Replay-driven E2E validation
- Clean separation between ingestion, rules, controls, adapters, and monitoring

## Architecture

```text
JSONL market/event replay feed
  -> Event parser
  -> Normalizer
  -> Rule engine
  -> Risk-style safety / approval controls
  -> Dry-run API adapter
  -> Audit log and monitoring snapshot
```

## Project Structure

```text
src/workflow_automation/
  adapters.py      Dry-run API adapter and payload generation
  controls.py      Approval queue and execution safety gate
  engine.py        E2E workflow orchestration
  feeds.py         JSONL event parsing and normalization
  models.py        Backend workflow domain models
  monitoring.py    Audit log and operational snapshots
  rules.py         Generic configurable rule evaluation

tests/
  test_adapters.py
  test_e2e_workflow.py
  test_feeds.py
  test_rules.py
```

## Run Tests

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

## Run Replay Example

```bash
PYTHONPATH=src python examples/replay_sample.py
```

## Testing Focus

The pytest suite validates:

- JSON event parsing and timestamp normalization
- Data transformation into typed backend models
- Business-rule outcomes such as approve, review, and reject
- Manual approval queue behavior
- Dry-run API payload generation
- Environment-style execution safety gates
- Replay-based E2E workflow behavior
- Monitoring snapshot counts and latest-state reporting

## Career Relevance

This project is designed to highlight backend quality engineering skills relevant to capital markets and trading technology roles:

- Python-based test automation
- Backend workflow validation
- REST/JSON payload validation
- Event-driven data processing
- Functional, integration, and E2E test design
- Risk-control and approval workflow testing
- Operational readiness patterns for controlled releases

## AI-Assisted Engineering

AI tools were used as engineering accelerators during project development:

- ChatGPT / OpenAI Codex for architecture planning
- Test scenario ideation and edge-case review
- Code review and refactoring support
- Documentation and technical storytelling

Implementation choices, validation, and final project structure were kept hands-on and reviewable.

## Notes

This is a public portfolio version. Futures strategy logic, proprietary research, credentials, account details, live execution settings, and sensitive operational data are intentionally excluded.
