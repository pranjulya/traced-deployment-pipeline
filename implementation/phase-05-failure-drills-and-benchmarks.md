# Phase 05 — Failure Drills And Benchmarks

Status: NOT_STARTED. Owner: learner + coding agent. Reviewer: main architect. No implementation performed.

## Goal
Measure overhead and rehearse incidents.
## Why
Reliability claims need fault evidence and repeatable experiments.
## Prerequisites
04 reviewed; environment recorded. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Stress failure isolation and identify resource ceilings without adding architecture.
## Files
future tests/failure/; benchmark harness; evidence reports. These are proposed future paths; create only those justified by the approved phase.
## Work sequence
1. Freeze environment, image/model/fixture revisions and protocol; separate fake-provider overhead from optional live-provider behavior.
2. Run alternating instrumentation-off/on measurements with warmup and three repetitions; preserve counts and failed attempts.
3. Inject provider timeout, tool failure, Collector loss, ledger disk/read-only failure and crashes around dispatch/commit.
4. Rehearse consistent backup restore and compatible image rollback; measure actual lost-data window and recovery time.
5. Give reviewer three blinded incidents, collect diagnosis timing, and publish missed targets with causes instead of erasing them.

## Tests
Three repeated baseline/on runs; crash boundaries; disk full; collector outage; restore.
## Deterministic test oracle
| Case | Expected result |
|---|---|
| Three paired overhead repetitions | Raw sanitized timing/count data and methodology retained; targets compared honestly |
| Crash before/after external dispatch | No invented zero charge; uncertainty retained; duplicate key never auto-replays |
| Disk fills during completion commit | 503 without answer; pending attempt preserved; readiness blocks new billable work |
| Collector prolonged outage | No accounting loss; trace-loss limitation and bounded memory recorded |
| Backup restore to clean volume | Integrity and registry/attempt consistency checked; RPO/RTO measured |
| Blinded provider/tool/release incident | Diagnosis steps and time recorded, including misses beyond 10 min |
| Privacy scan after faults | Canary absence verified across exceptional paths and evidence exports |

## Failure scenarios
Telemetry backpressure; retry amplification; corrupted backup; total host loss.
## Acceptance criteria
R04/R07 verified under faults; budgets pass or explicit review records miss; RTO/RPO measured. No result may be marked passing without recorded output.
## Learning objectives
Read distributions and distinguish evidence from extrapolation.
## Interview questions
What can a single-host monitoring stack never observe reliably? Answer using this phase's measured evidence and the relevant Learning page.
## Review gate and rollback
Check requirement mapping, privacy, bounded resource use and changed contracts. Revert this phase's app/config changes if its checks fail; preserve ledger data and avoid incompatible migrations. A rollback requiring data transformation needs a tested backup first.
## Completion record
Implementation commit: pending. Commands/results: pending. Evidence paths: pending. Deviations: pending. Review decision: pending. Next phase authorization: pending.
