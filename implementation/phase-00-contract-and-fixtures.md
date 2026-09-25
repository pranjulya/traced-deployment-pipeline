# Phase 00 — Contract And Fixtures

Status: TESTED — awaiting G1 review. Owner: learner + coding agent. Reviewer: main architect. No application code written.

## Goal
Freeze the operational contract before code.
## Why
Avoid confusing dashboard appearance with system correctness.
## Prerequisites
G0 scope review; local host inventory. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Select bounded interfaces, ADRs, price fixture and privacy schema.
## Files
docs/product/PRD.md; docs/architecture/*; tests/fixtures/ (created). Produced: docs/architecture/versions-and-pins.md; tests/fixtures/prices.json, cases.json, canaries.json, telemetry-allowlist.json; tests/test_fixture_oracle.py.
## Work sequence
1. Read master, applicable ADRs and predecessor evidence; restate the contract.
2. Define the smallest deterministic check for this phase's success and failure cases.
3. Implement only the phase boundary; preserve earlier acceptance checks.
4. Run checks, record actual evidence and explain one representative failure to the reviewer.
## Tests
Review deterministic expected runs, cost examples and threat cases.
## Failure scenarios
Missing GPU/provider; insufficient RAM; unsupported histogram integration.
## Acceptance criteria
ADR choices recorded; fixture oracle reviewed; versions and resource budget selected. No result may be marked passing without recorded output.
## Learning objectives
Explain metrics versus traces versus ledger truth.
## Interview questions
Why must accounting survive trace loss? Answer using this phase's measured evidence and the relevant Learning page.
## Review gate and rollback
Check requirement mapping, privacy, bounded resource use and changed contracts. Revert this phase's app/config changes if its checks fail; preserve ledger data and avoid incompatible migrations. A rollback requiring data transformation needs a tested backup first.
## Completion record
Implementation commit: `6537e76` (phase-00 contract and fixtures; no application code).
Commands/results (run 2026-09-25 on host Python 3.9.6):
- `python3 tests/test_fixture_oracle.py` → `Ran 19 tests ... OK`.
- `python3 -m unittest discover -s tests -p 'test_*.py'` → `Ran 19 tests ... OK`.
- Image pins resolved from the Docker Hub tag API; all seven images publish an `arm64` variant (see docs/architecture/versions-and-pins.md).
Evidence paths: tests/fixtures/; tests/test_fixture_oracle.py; docs/architecture/versions-and-pins.md.
Deviations: the reference host is macOS/Docker Desktop per G0 instead of Linux; the Docker Desktop daemon was not running, so pins were resolved via the registry API and must be re-verified by digest at pull in Phase 02.
Representative failure reviewed: the first oracle run exposed an over-strict invariant — `price-lookup-miss` has provider-observed usage but an unknown charge. The check was corrected to treat `charge_state` and `usage_origin` as independent while still forbidding any numeric charge when `charge_state` is unknown. This is the "known usage, unknown price" versus "unknown usage, unknown charge" distinction.
Acceptance criteria status: ADR choices recorded (G0); versions and resource budget selected (versions-and-pins.md); fixture oracle present and internally consistent (19 checks pass).
Review decision: pending G1 — fixtures and expected failure behavior must be reviewed before Phase 01 code.
Next phase authorization: pending G1 review; Phase 01 must not start before it.
