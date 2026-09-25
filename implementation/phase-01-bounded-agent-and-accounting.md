# Phase 01 — Bounded Agent And Accounting

Status: COMPLETE (G2 approved 2026-09-25). Owner: learner + coding agent. Reviewer: main architect.

## Goal
Build minimal bounded workload and durable usage path.
## Why
Failures must have a stable reproducible source.
## Prerequisites
00 approved; fake-provider fixture oracle. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Introduce API, provider interface, read-only tool, deadline and local ledger.
## Files
Created: app/config.py, money.py, pricing.py, prices.json, accounting.py, providers.py, tools.py, agent.py, api.py; requirements.txt, requirements-dev.txt; tests/conftest.py, test_money.py, test_pricing.py, test_accounting.py, test_agent_oracle.py, test_api.py. Run on Python 3.12 venv (pinned fastapi 0.141.1, uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1).
## Work sequence
1. Specify authenticated request/error contracts, principal mapping and key alphabet before implementing handlers.
2. Create run-registry and attempt-ledger migrations with uniqueness constraints; review crash windows and retention semantics.
3. Implement atomic admission, fixed duplicate response, bounded concurrency and deadlines around the deterministic provider.
4. Add read-only lookup and per-attempt accounting; withhold output on failed completion commit.
5. Verify restart classification and inspect stored rows for absent raw keys, prompts and answers.

## Tests
Validate input/auth, timeout, attempt limits, duplicate keys, decimal totals and crash recovery.
## Deterministic test oracle
| Case | Expected result |
|---|---|
| Missing key or bad authentication | 400 or 401 respectively; zero registry execution and zero provider calls |
| Two concurrent requests, same principal/key | One admission/provider execution; duplicate gets 409 metadata |
| Same key with different valid body | 409, new body ignored, no second call |
| Different principal with same key | Separate namespace; permitted only through trusted server credential mapping |
| Terminal record after 24 h and pruning | Same key may execute anew; expiry behavior documented |
| Unresolved record older than 24 h | Retained; duplicate blocked; no silent reexecution |
| Failure to commit pending attempt | No external call; 503 accounting unavailable |
| Completion commit failure after provider result | Answer withheld; 503 plus run_id; durable pending state recoverable |
| Restart with unresolved attempt | Unknown state visible; no automatic redispatch |
| Retryable provider fault followed by success | Each actual attempt counted once; at most three attempts within total deadline |

## Failure scenarios
Provider completes before ledger commit; duplicate completion; unknown usage.
## Acceptance criteria
R01/R04 pass; no new call after failed pending commit; uncertainty visible. No result may be marked passing without recorded output.
## Learning objectives
Trace external side effects across transaction boundaries.
## Interview questions
Can an idempotency key guarantee exactly-once provider billing? Answer using this phase's measured evidence and the relevant Learning page.
## Review gate and rollback
Check requirement mapping, privacy, bounded resource use and changed contracts. Revert this phase's app/config changes if its checks fail; preserve ledger data and avoid incompatible migrations. A rollback requiring data transformation needs a tested backup first.
## Completion record
Implementation commit: `93666a0`.
Commands/results (2026-09-25, `.venv` Python 3.12):
- `.venv/bin/python -m pytest tests -q` → `57 passed`.
- `python3 tests/test_fixture_oracle.py` → `Ran 24 tests ... OK` (oracle unchanged and re-verified).
Evidence paths: app/; tests/; requirements.txt; docs/architecture/accounting-and-api-contract.md.
Requirement mapping: R01 (bounded authenticated request with fake provider and read-only tool, 30 s deadline, max 3 attempts / 2 tool calls); R04 (unsampled attempt-level usage and charge with observed/unknown states).
Failure handling: pending-commit failure makes no external call and returns 503; completion-commit failure withholds the answer, keeps the pending attempt recoverable and returns 503 with run_id; timeout becomes unknown (never zero); restart classifies pending attempts as unknown and proves no-dispatch runs as failed; transport/auth/schema errors are not retried.
Security/privacy: bearer secret compared with `hmac.compare_digest`; idempotency key stored only as a principal-scoped HMAC digest; request bodies, prompts and answers are never written to the ledger (verified by a stored-row scan); readiness requires a writable ledger and valid secrets.
Deviations: (1) contract correction discovered while implementing — the retry oracle declared a different success token count (400) than the deterministic provider returned (500); the fixture was standardised to 1000/500 for all successes and re-verified, and `money.rule` was added to app/prices.json to match the frozen fixture. This is a Phase 00 fixture correction, recorded here and re-tested. (2) The reference host is macOS/Docker Desktop per G0; Docker Desktop was not running, but Phase 01 runs from the pinned local Python 3.12 venv, so no container was needed.
Rollback impact: reverting this phase removes app/ and the Phase 01 tests and restores prior requirements files; the ledger schema is additive and no migration runs in reverse, so existing ledger data is preserved.
Review decision: APPROVED at G2 on 2026-09-25 (owner/main architect) — requirement mapping, evidence, failure handling, rollback impact and privacy accepted. Phase 01 marked COMPLETE.
Next phase authorization: Phase 02 authorized 2026-09-25.
