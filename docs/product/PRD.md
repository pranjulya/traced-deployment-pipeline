# Product requirements
Status: APPROVED_AT_G0 (2026-09-25); targets proposed, not achieved.

## User and outcome
A developer/operator needs to answer “why was this agent slow or expensive, what failed, and which release caused it?” from one local reproducible deployment. Recruiters/reviewers need reproducible evidence, not screenshots alone.

## V1 behavior and requirements
| ID | Requirement | Verification / phase |
|---|---|---|
| R01 | Bounded authenticated read-only request with fake provider and local lookup; 30 s total deadline, maximum 3 provider attempts and 2 tool calls | boundary/deadline checks / 01 |
| R02 | Pinned single-host Compose deployment with health/readiness, persistent accounting and documented rollback | clean start/restart/rollback / 02 |
| R03 | Request root with provider-attempt and tool child spans preserves actual execution parentage and safe correlation identifiers | trace fixture / 03 |
| R04 | Unsampled usage and charge records distinguish observed, estimated, unknown and reconciled | crash/duplicate/retry tests / 01,05 |
| R05 | Dashboard shows latency, errors, throughput, saturation, usage, charge coverage and telemetry drops | fixture reconciliation / 04 |
| R06 | Actionable service and pipeline alerts include runbook; local sink proves receipt and recovery | timed drill / 04,05 |
| R07 | No prompts, outputs, tool arguments, secrets or user identifiers in telemetry | canary scan / 03,05 |
| R08 | A new reviewer can repeat deployment, benchmark and incident diagnosis | clean-machine rehearsal / 06 |

## Service envelope
Single operator, one API process, one reference host (macOS 26.5, Apple M4 Mac mini, Docker Desktop Linux container runtime, arm64), up to 10 concurrent synthetic requests. Provisional fake-provider baseline: 100 requests, 2 concurrent, no injected faults, p95 response under 1 s; full-stack overhead under 15% median latency and 20% p95 versus equivalent uninstrumented fixture after warmup. Real-provider latency is reported separately. Metrics scrape every 15 s; sustained service error alert condition 2 minutes plus delivery under 60 s. These are reviewable budgets, not SLAs.

## Non-goals
High availability, multi-tenant billing, exactly-once external provider charges, unrestricted agents, Kubernetes, automatic remediation, public dashboard access, capturing model content, and integration dependency on other portfolio projects.

## User journey
Start documented stack → authenticate synthetic request → inspect correlation ID → inspect request trace and safe error code → compare usage ledger with dashboard → inject provider timeout → receive local alert → follow runbook → rollback if regression → save sanitized evidence.

## Acceptance and open approvals
Approved at G0 (2026-09-25): reference host and resource envelope, provider choice (fake default), dashboard retention and the destination for later real notifications. New-provider spending and any real notification destination remain separately approval-gated.
