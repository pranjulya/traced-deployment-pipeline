# Interview questions and answers

**Why separate billing from traces?** Traces can be sampled, dropped or delayed. Durable attempt-level usage records preserve accounting state independently; unknown external outcomes remain explicit.

**Does idempotency provide exactly-once billing?** No. It prevents local duplicate dispatch for an accepted key, but a crash around an external provider call can leave uncertainty. Provider-supported idempotency or reconciliation may help; never infer remote facts from local state alone.

**Why Compose rather than Kubernetes?** The scope is a reproducible single-host operations reference. Kubernetes adds an orchestration learning objective without removing the need for correct telemetry or accounting. Scale and availability requirements would justify revisiting it.

**How is a slow request diagnosed?** Use latency and error panels to identify the affected operation and release, then a retained correlated trace to split provider, retries and tool time. If sampling removed the trace, use aggregates and a safe reproduction rather than fabricate causality.

**What is the privacy strategy?** Collect only fixed metadata and counts. Disable body/header capture and raw exception strings; test all sinks with synthetic canaries. Restrict observability access and retention.

**Why can a local model still cost money?** Provider API fees may be zero; host rental, electricity and operations remain costs. Show them separately, with uncertainty and methodology.

**What does a passing alert test prove?** A known injected signal reached the configured sink and later resolved. It does not prove notification during total host failure; that needs an independent observer.

**When would SQLite be replaced?** When replicas, write contention or retention volume exceed measured limits. Preserve attempt uniqueness, crash semantics and reconciliation before moving to a shared database.

**What evidence makes this production-grade learning?** Reproducible deployment, negative checks, privacy tests, bounded failure behavior, restore/rollback evidence and honest limitations. The current planning package contains no achieved reliability or benchmark claims.
