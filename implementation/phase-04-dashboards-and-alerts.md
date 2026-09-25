# Phase 04 — Dashboards And Alerts

Status: NOT_STARTED. Owner: learner + coding agent. Reviewer: main architect. No implementation performed.

## Goal
Turn signals into actionable diagnosis and notification.
## Why
Data without operating decisions does not prove production debugging.
## Prerequisites
03 reviewed; synthetic known totals available. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Grafana views and Prometheus rules → Alertmanager → local sink.
## Files
future dashboards/; alerts/; notification fixture; runbooks. These are proposed future paths; create only those justified by the approved phase.
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
Implementation commit: pending. Commands/results: pending. Evidence paths: pending. Deviations: pending. Review decision: pending. Next phase authorization: pending.
