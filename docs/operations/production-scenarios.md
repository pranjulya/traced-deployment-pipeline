# Production scenarios and runbooks

| Scenario | Detection | Immediate action | Recovery proof |
|---|---|---|---|
| Provider timeout/retry storm | timeouts, attempt/request ratio, provider spans | cap concurrency; confirm deadline and retry budget | bounded attempts and service latency recover |
| Tool exception | typed tool error span and outcome counter | reproduce with fixture key; reject unsafe fallback | known fixture succeeds, no payload leak |
| Collector unavailable | export drops/queue growth, backend gap | keep serving within bounded queue; restore collector | fresh traces arrive; accounting reconciles despite trace gap |
| Ledger volume read-only/full | ledger error and disk signal | reject new billable requests; free/restore volume safely | integrity check and pending-attempt review pass |
| Crash after provider call | unresolved pending attempt | mark uncertainty; reconcile provider record if available | unknown remains explicit until evidence resolves it |
| Bad release | health regression and release annotation | deploy pinned prior image compatible with current schema | smoke request and ledger consistency pass |
| Host dies | external observer only, absent by default | restore host from documented backup | measured RTO/RPO and lost-data window recorded |
| Alert destination down | delivery error and local sink drill | inspect routing and retry state | test alert received once and resolved |

Rehearsal record includes start time, injection, expected signal, observed detection time, diagnosis steps, action, recovery time, unknowns and sanitized evidence. Proposed backup every 24 h, RPO ≤24 h and RTO ≤30 min for the tiny reference dataset; these become claims only after restore tests. SQLite backups must use a consistent backup mechanism, not an arbitrary copy of a live WAL file.
