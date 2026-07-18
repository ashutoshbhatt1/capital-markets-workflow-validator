# Repository guide

## Product invariant

The deterministic validator and human reviewer own every decision. AI may explain supplied evidence and recommend tests only. Never add an AI-controlled execution, approval, configuration, or order-routing path. `execution_authorized` must remain false.

## Commands

- Python tests: `pytest -q`
- Replay: `PYTHONPATH=src python examples/run_guardian_demo.py --scenario limit-breach`
- Web checks: `cd web && npm run lint && npm test`

## Conventions

- Keep examples synthetic and sanitized.
- Keep credentials in environment variables and never commit `.env.local`.
- Add tests for changes to a safety boundary or API contract.
- Preserve fixture mode so judges can evaluate the complete experience without a key.
