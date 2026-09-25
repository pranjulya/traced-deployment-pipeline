# P09 runbooks

Each alert annotation links to one section here. Runbooks describe detection,
immediate action, recovery proof and the honest limits of a single host.

## service-errors
- Detection: `P09ServiceErrorRateHigh` (5xx share > 5% with ≥ 20 requests in 5m, sustained 2m).
- Immediate action: check the Error budget and per-operation panels; inspect a retained `agent.run` trace; confirm it is not a false positive from very low traffic.
- Recovery proof: 5xx share back under 5% for 2m with sample counts still visible.
- Limit: if the request volume is below the 20-request minimum, no page fires by design.

## provider-timeouts
- Detection: `P09ProviderTimeoutRateHigh` (timeout share of provider attempts > 5%, same minimum traffic).
- Immediate action: cap concurrency; confirm the 30 s deadline and 3-attempt budget; find the affected model/provider spans.
- Recovery proof: bounded attempts and recovered service latency; ledger shows unknown charges rather than zeros.
- Limit: a timed-out call may still have been billed; uncertainty is surfaced, not resolved.

## ledger-write-failure
- Detection: `P09LedgerWriteFailure` (any ledger commit failure, immediate).
- Immediate action: treat new billable work as blocked; check disk and volume writability; follow the deployment runbook to restore the ledger safely.
- Recovery proof: repeated duplicate key returns 409 metadata, not a new dispatch; pending attempts reconciled with an audit record.
- Limit: while the ledger is unwritable the service returns 503 by design rather than risking an unaccounted call.

## telemetry-drops
- Detection: `P09TelemetryDrops` (any export drop over 5m).
- Immediate action: check the Collector queue, memory limiter and Tempo availability; confirm the app is still serving.
- Recovery proof: drops return to zero and fresh traces arrive; accounting totals are unchanged.
- Limit: trace loss is acceptable for diagnostics; it must never be used to infer cost.

## disk-space-low
- Detection: `P09DiskSpaceLow` (root filesystem free < 15% for 5m).
- Immediate action: free space or expand the volume; check ledger WAL growth and telemetry retention (traces 24h, metrics 7d).
- Recovery proof: free space above threshold; ledger integrity check passes.
- Limit: a full disk stops billable work, not telemetry-only ingestion.

## heartbeat-absent
- Detection: `P09HeartbeatAbsent` (`absent(up{job="p09-api"}[2m])`).
- Immediate action: check the host and container state; if the whole host is down, the local stack cannot alert from itself.
- Recovery proof: scrape resumes and the alert resolves.
- Limit: a fully failed host requires an external observer (below); this is not covered locally.

## alert-delivery
- Detection: Alertmanager delivery failures (`send_resolved: true`, local sink receipt missing).
- Immediate action: verify the sink is reachable, inspect Alertmanager routing and retry state.
- Recovery proof: a test alert is received once and later resolves at the sink.
- Limit: firing is not receipt; only the sink confirms delivery.

## host-failure blind spot
A fully failed single host cannot observe or notify its own failure. The local
Prometheus/Alertmanager/Grafana stack, the ledger and the sink all stop with it.
Robust detection requires a separately deployed external observer (a later,
explicitly authorized external requirement) and is intentionally out of scope
here. Restore is via the documented backup (RPO ≤ 24h, RTO ≤ 30 min, measured
only after a restore test).
