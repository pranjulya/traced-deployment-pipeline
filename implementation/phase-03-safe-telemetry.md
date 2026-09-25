# Phase 03 — Safe Telemetry

Status: IMPLEMENTED / TESTED (SDK and config side) — live Collector/Tempo verification BLOCKED (Docker unavailable). Owner: learner + coding agent. Reviewer: main architect.

## Goal
Add correlated spans and bounded content-free signals.
## Why
Operators need causes without retaining sensitive content.
## Prerequisites
02 reviewed; schema allowlist frozen. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
OTel SDK → Collector → Tempo; Prometheus application metrics.
## Files
Created: app/telemetry.py (allowlist enforcement, bounded exporter, head sampling, drop accounting, Prometheus metrics); app/telemetry-allowlist.json; deploy/collector/collector-config.yaml; instrumentation in app/agent.py, app/api.py (/metrics), app/main.py; tests/telemetry/test_telemetry.py, tests/telemetry/test_collector_config.py.
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
Implementation commit: `c557278`.
Commands/results (2026-09-25, `.venv` Python 3.12):
- `.venv/bin/python -m pytest tests -q` → `81 passed` (57 Phase 01 + 10 deploy-config + 10 telemetry + 4 collector-config).
- Live Collector/Tempo checks NOT RUN: Docker Desktop engine unavailable (Phase 02 blocker, unchanged).
Evidence paths: app/telemetry.py; app/telemetry-allowlist.json; deploy/collector/collector-config.yaml; tests/telemetry/.
Requirement mapping: R03 (agent.run root with provider.attempt and tool.lookup children that follow actual execution parentage — asserted by span id), R07 (no prompts, outputs, tool arguments, secrets or identifiers in telemetry — canary scan across SDK span output, span/event attributes, metric text and captured logs).
Failure handling: export endpoint down is non-blocking and counted (`spans_dropped > 0`) while the request still completes and the ledger stays correct; the SDK exporter uses a bounded queue (`max_queue`) and never raises into the request path; head sampling at 10% reduces retained traces while all 60 runs' charges remain in the unsampled ledger.
Privacy hardening: `start_as_current_span(record_exception=False, set_status_on_exception=False)` prevents OTel from attaching exception messages; non-allowlisted attributes are dropped and counted (`dropped_attributes`); metrics carry only `route_template`, `operation`, `outcome`, `model_alias`; no run/trace ids or principals.
Deviations: (1) Phase 03 opened while Phase 02 is not COMPLETE — the owner explicitly authorised proceeding with daemon-independent work because the only blocker is Docker Desktop; (2) live Collector ingestion, Tempo storage, Collector queue saturation and the Prometheus scrape path remain unverified until Docker is available; (3) the 10%-head-sampling comparison is asserted for traces vs accounting, not yet for a live backend.
Rollback impact: reverting removes app/telemetry.py, the collector config and the telemetry tests and restores prior instrumentation; the ledger schema is unchanged.
Review decision: pending — cannot be marked COMPLETE until the live Collector/Tempo checks run and both Phase 02 and Phase 03 are reviewed.
Next phase authorization: withheld pending live verification.
