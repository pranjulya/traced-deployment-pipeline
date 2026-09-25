# Phase 03 — Safe Telemetry

Status: NOT_STARTED. Owner: learner + coding agent. Reviewer: main architect. No implementation performed.

## Goal
Add correlated spans and bounded content-free signals.
## Why
Operators need causes without retaining sensitive content.
## Prerequisites
02 reviewed; schema allowlist frozen. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
OTel SDK → Collector → Tempo; Prometheus application metrics.
## Files
future app/telemetry.py; deploy/collector assets; tests/telemetry/. These are proposed future paths; create only those justified by the approved phase.
## Work sequence
1. Enumerate every allowed span attribute, event field and metric label; disable broad automatic body/header/exception capture.
2. Instrument run root, provider-attempt children and tool children according to actual control flow; propagate safe generated context.
3. Configure bounded SDK/Collector export queues and safe drop indicators; start unsampled at fixture scale.
4. Validate privacy at SDK output, Collector, Tempo, metrics, application logs and notification payloads.
5. Compare 100% and 10% head sampling with identical accounting fixtures and explicitly record trace gaps.

## Tests
Expected parentage, safe error codes, canary scan, exporter outage and queue saturation.
## Deterministic test oracle
| Case | Expected result |
|---|---|
| Success with tool and two provider attempts | One run root and correct child relations; no invented nesting |
| Canary in prompt, tool args, header and exception | Zero occurrences in every telemetry sink |
| User-supplied correlation/label value | Rejected/replaced by trusted bounded schema; no unbounded labels |
| Export endpoint down and queue saturated | Bounded memory; drop signal; workload still completes within stated budget |
| 10% head sampling | Fewer retained traces; no promise all errors retained; unchanged ledger totals |
| Metrics inspect | No run IDs, trace IDs, raw keys or content labels |

## Failure scenarios
Lost context across retry; automatic header capture; high-cardinality labels.
## Acceptance criteria
R03/R07 pass; metrics/ledger unsampled; export loss visible and nonblocking. No result may be marked passing without recorded output.
## Learning objectives
Explain cardinality, propagation and head sampling limitations.
## Interview questions
Why cannot head sampling promise retention of every failed request? Answer using this phase's measured evidence and the relevant Learning page.
## Review gate and rollback
Check requirement mapping, privacy, bounded resource use and changed contracts. Revert this phase's app/config changes if its checks fail; preserve ledger data and avoid incompatible migrations. A rollback requiring data transformation needs a tested backup first.
## Completion record
Implementation commit: pending. Commands/results: pending. Evidence paths: pending. Deviations: pending. Review decision: pending. Next phase authorization: pending.
