# Phase 04 — Dashboards And Alerts

Status: IMPLEMENTED / TESTED (assets and delivery path) — live Prometheus/Grafana/Alertmanager verification BLOCKED (Docker unavailable). Owner: learner + coding agent. Reviewer: main architect.

## Goal
Turn signals into actionable diagnosis and notification.
## Why
Data without operating decisions does not prove production debugging.
## Prerequisites
03 reviewed; synthetic known totals available. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Grafana views and Prometheus rules → Alertmanager → local sink.
## Files
Created: dashboards/p09-overview.json; alerts/prometheus-rules.yaml; alerts/alertmanager.yaml; deploy/sink/notify_sink.py; deploy/fixtures/load_ledger_fixture.py; docs/operations/runbooks.md; ledger aggregate metrics (p09_known_charge_nano_total, p09_unknown_attempts, p09_usage_coverage_ratio) and p09_ledger_write_failures_total; tests/ops/.
## Work sequence
1. Load deterministic known usage, unknown attempts and multiple currencies into the fixture ledger.
2. Build service, provider/tool latency, resource and accounting panels with counts and explicit uncertainty labels.
3. Write actionable alert rules with minimum traffic, sustained windows and linked runbooks.
4. Route only to a local sink; test firing, grouping, silence, receiver failure and resolution.
5. Record which signals disappear on complete host failure and identify the separately required external observer.

## Tests
Panel totals vs ledger, histogram counts, alert firing/resolution, grouping and delivery.
## Deterministic test oracle
| Case | Expected result |
|---|---|
| Fixture totals with known/unknown charges | Dashboard matches ledger after scrape delay; unknown shown separately |
| Two currencies | Separate totals; never a mixed currency sum |
| Low/no traffic | No misleading error-rate page; sample counts visible |
| Sustained eligible error fixture | Fires after defined window; local receipt within 60 s of firing |
| Recovery | Resolution reaches local sink and clears active alert |
| Sink outage | Delivery failure visible; firing state not mistaken for receipt |
| Repeated same alert | Grouping/deduplication works without per-request cardinality |
| Entire host down | Documented local visibility limitation, no false assertion of notification |

## Failure scenarios
Zero traffic; low sample count; receiver down; mismatched currencies.
## Acceptance criteria
R05/R06 pass; each alert maps to a runbook; unknown cost displayed separately. No result may be marked passing without recorded output.
## Learning objectives
Differentiate alert condition, routing, delivery and acknowledgment.
## Interview questions
How do you detect a broken alert pipeline? Answer using this phase's measured evidence and the relevant Learning page.
## Review gate and rollback
Check requirement mapping, privacy, bounded resource use and changed contracts. Revert this phase's app/config changes if its checks fail; preserve ledger data and avoid incompatible migrations. A rollback requiring data transformation needs a tested backup first.
## Completion record
Implementation commit: `4ace7c7`.
Commands/results (2026-09-25, `.venv` Python 3.12):
- `.venv/bin/python -m pytest tests -q` → `102 passed` (57 Phase 01 + 10 deploy-config + 10 telemetry + 4 collector-config + 21 Phase 04 ops checks).
- Live Prometheus rule evaluation, Grafana rendering and Alertmanager grouping/delivery NOT RUN: Docker Desktop engine unavailable (unchanged blocker).
Evidence paths: dashboards/p09-overview.json; alerts/; deploy/sink/; deploy/fixtures/; docs/operations/runbooks.md; tests/ops/.
Requirement mapping: R05 (latency/errors/throughput/saturation/usage/coverage/drop panels, fixture totals reconciled to the ledger, unknown charge shown separately, currencies never summed), R06 (actionable alerts with severity/owner/service/runbook, minimum traffic + sustained window, local sink receipt and resolution).
Failure handling: receiver-down is detectable rather than silent; grouping uses only alertname/service/severity (no per-request cardinality); low/no traffic does not page because the error and timeout rules require >= 20 events; the whole-host-down blind spot is documented with the external-observer requirement.
Privacy: no alert labels, annotations, dashboard queries or metric labels contain run/trace ids, principals or payloads (asserted).
Deviations: (1) Phase 04 opened while Phases 02/03 are not COMPLETE — owner-authorized daemon-independent work; (2) live rule firing, delivery latency (<60s), grouping, silence and Grafana rendering remain unverified until Docker is available; (3) node/disk panels depend on node_exporter, which is not yet added to Compose.
Rollback impact: reverting removes dashboards/, alerts/, the sink, the fixture loader and the ops tests and restores prior metrics code; the ledger schema is unchanged.
Review decision: pending — cannot be marked COMPLETE until live Prometheus/Grafana/Alertmanager checks run and Phases 02–04 are reviewed.
Next phase authorization: withheld pending live verification.
