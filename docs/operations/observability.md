# Observability operating contract

## Signals and retention
API emits request rate, outcomes, latency histogram, in-flight requests, provider attempts, timeout count and tool outcomes. Collector/exporter exposes queue utilization and drops. Ledger aggregates emit known charge total, unknown-attempt count, reconciliation lag and usage coverage; dashboards label currency and price version. Do not sum different currencies. Proposed retention: traces 24 h, metrics 7 days, ledger 30 days; validate disk use and erase test data after review.

Dashboard panels: service health, p50/p95/p99 with sample counts, retry amplification, provider/tool split, CPU/RAM/disk, telemetry loss, known versus unknown costs, and release annotation. Low counts must remain visible so percentile panels do not imply statistical confidence. Trace links use exemplars where supported; absent sampled trace links are expected.

## Alerts
Service errors >5% with at least 20 requests in 5 minutes, sustained 2 minutes; timeout rate >5% at same minimum; disk free <15% for 5 minutes; ledger write failure immediately; telemetry drops >0 for 5 minutes; absent heartbeat for 2 minutes. Each includes severity, owner, affected service, dashboard link, safe context and runbook. Thresholds are provisional and tuned using drills. Deduplicate and group by service/outcome, never run ID. Recovery notifications are exercised.

Local webhook sink is the default destination. Real email/chat delivery requires a chosen destination and authorization during implementation. Test the entire signal → rule → Alertmanager → sink path. A fully failed host cannot alert from itself; an external heartbeat is a later explicit deployment requirement, not falsely covered by the local stack.
