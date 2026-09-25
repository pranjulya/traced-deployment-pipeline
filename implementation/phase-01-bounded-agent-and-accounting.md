# Phase 01 — Bounded Agent And Accounting

Status: NOT_STARTED. Owner: learner + coding agent. Reviewer: main architect. No implementation performed.

## Goal
Build minimal bounded workload and durable usage path.
## Why
Failures must have a stable reproducible source.
## Prerequisites
00 approved; fake-provider fixture oracle. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Introduce API, provider interface, read-only tool, deadline and local ledger.
## Files
future app/api.py, agent.py, providers.py, accounting.py; tests/. These are proposed future paths; create only those justified by the approved phase.
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
Implementation commit: pending. Commands/results: pending. Evidence paths: pending. Deviations: pending. Review decision: pending. Next phase authorization: pending.
