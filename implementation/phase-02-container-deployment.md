# Phase 02 — Container Deployment

Status: NOT_STARTED. Owner: learner + coding agent. Reviewer: main architect. No implementation performed.

## Goal
Make a clean local deployment repeatable.
## Why
An unreproducible demo cannot support reliable operations.
## Prerequisites
01 reviewed; Docker Desktop running on the macOS reference host (arm64 Linux container runtime). All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Internal networks, persistent ledger, bounded resources and pinned images.
## Files
future deploy/; deployment runbook; tests/integration/. These are proposed future paths; create only those justified by the approved phase.
## Work sequence
1. Record runtime/image compatibility against Docker Desktop on arm64 and pin candidate digests; define separate private ingress and telemetry networks.
2. Package the API without embedded secrets; mount writable ledger and inject application/provider/HMAC credentials separately.
3. Define readiness around valid configuration and writable ledger; define resource/concurrency caps.
4. Write fresh-volume bootstrap, consistent backup, restart and prior-image rollback procedures.
5. Rehearse migration compatibility before any ledger schema change is accepted.

## Tests
Clean start, readiness, volume restart, non-root execution and prior-image rollback.
## Deterministic test oracle
| Case | Expected result |
|---|---|
| Clean host and fresh volume | Documented start reaches ready; one authenticated fixture completes |
| Container recreation | Ledger/run registry retained; duplicate key does not redispatch |
| Missing HMAC or application secret | Startup/readiness fails safely; no provider calls |
| Read-only ledger volume | Not ready; new execution rejected, existing evidence preserved |
| Collector unavailable | Application readiness remains independent |
| Prior image with compatible schema | Smoke execution works and totals remain consistent |
| Incompatible schema rollback | Procedure refuses unsafe downgrade; tested backup path required |
| Inspect host ports and image environment | No public admin services or baked-in secrets |

## Failure scenarios
Read-only volume; missing secret; incompatible schema; host memory pressure; Docker Desktop daemon stopped or VM under-allocated.
## Acceptance criteria
R02 passes; rollback and persistent accounting verified; no public admin ports. No result may be marked passing without recorded output.
## Learning objectives
Distinguish readiness from liveness and recoverability from HA.
## Interview questions
Why should Collector failure not fail application readiness? Answer using this phase's measured evidence and the relevant Learning page.
## Review gate and rollback
Check requirement mapping, privacy, bounded resource use and changed contracts. Revert this phase's app/config changes if its checks fail; preserve ledger data and avoid incompatible migrations. A rollback requiring data transformation needs a tested backup first.
## Completion record
Implementation commit: pending. Commands/results: pending. Evidence paths: pending. Deviations: pending. Review decision: pending. Next phase authorization: pending.
