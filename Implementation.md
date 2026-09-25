# Project 09 — Traced Deployment Pipeline

Status: G0/G1/G2 approved. Phase 00, 01 COMPLETE; Phase 02 IMPLEMENTED (live rehearsal BLOCKED: Docker Desktop unavailable); Phase 03 IMPLEMENTED/TESTED (SDK+config; live Collector/Tempo BLOCKED by the same); phases 04–06 NOT_STARTED. Owner: learner/main architect. Last reviewed: 2026-09-25.

## Product contract
Build a reproducible single-host reference deployment of a bounded read-only agent, then prove that an operator can diagnose provider, tool, deployment, and telemetry failures using correlated traces, operational metrics, durable usage accounting, dashboards, and actionable alerts. This is a production-minded learning deployment, not a high-availability service claim.

## Authority and reading order
This file is the master scope/status source. Read docs/product/PRD.md, docs/architecture/HLD.md, docs/evaluation/evaluation-strategy.md, docs/architecture/LLD.md, proposed ADRs, then the active phase. Evaluation is designed before detailed implementation. A conflict stops the phase until this master and affected documents are reconciled. Nothing in these plans authorizes implementation, external deployment, purchases, or alert messages.

## Recommended defaults and unresolved decisions
Python API service; deterministic fake provider and one local read-only lookup tool first. Docker Compose on one macOS reference host (Apple Silicon arm64) using Docker Desktop's Linux container runtime; OpenTelemetry SDK/Collector, Prometheus, Grafana, Tempo, Alertmanager candidate stack. SQLite WAL on a named local volume for unsampled usage accounting. No queue, Kubernetes, hosted telemetry, or autonomous write tools in V1. Versions/images are chosen and pinned during phase 00, never assumed here; every pinned image must publish an arm64 variant.

The reference host is a Mac mini (Apple M4, 16 GB RAM, macOS 26.5) running Docker Desktop. Docker Desktop must be configured to grant the stack at least the proposed 4 vCPU/8 GB allocation; verify the allocation before adding components and measure actual use before claiming the budget. Paid-provider demonstration is optional, capped at a proposed USD 5 total, and requires later approval. Projects 08 and 10 are optional adapters only. A fake provider makes this project independently runnable. API fees for P08 are zero, but compute/electricity are separately estimated and never silently zeroed.

## G0 approval record
Approved 2026-09-25 by the owner (learner/main architect).
- Scope and PRD: approved.
- Reference host: macOS 26.5 on an Apple M4 Mac mini (16 GB RAM), Docker Desktop Linux container runtime (arm64).
- Resource envelope: proposed 4 vCPU / 8 GB Docker Desktop allocation; measure before adding components.
- Stack candidates: Compose + OTel Collector + Tempo + Prometheus + Grafana + Alertmanager + SQLite WAL; exact versions/digests pinned in phase 00.
- Provider: deterministic fake provider by default; optional real-provider spend capped at USD 5 and requiring separate approval.
- Retention: traces 24 h, metrics 7 days, ledger 30 days.
- Authentication: a single injected application secret mapped to the `demo-operator` principal.
- ADRs 001–004: ACCEPTED.
- Publication: no push to a public remote, external deployment or notification without separate authorization (Review gate G3).
- Phase 00 is authorized to open; fixtures and expected-failure behavior still require G1 review before Phase 01 code.

## Dependency map
00 Contract & fixtures → 01 Agent & accounting → 02 Container deployment → 03 Telemetry → 04 Dashboards & alerts → 05 Failure drills → 06 Release evidence.
Each phase depends on all preceding acceptance gates. No parallel product implementation until interfaces stabilize.

## Review gates
G0: owner approves PRD, scope, budgets, environment and ADR choices before coding. G1: tests/fixtures and expected failure behavior reviewed before implementation. G2: phase evidence, privacy checks, rollback and learning explanation reviewed before phase completion. G3: independent release review and rehearsal before any external deployment or publication.

## Definition of Done
Every requirement has a passing check and evidence path; negative cases exercised; telemetry contains no payload/secret canaries; accounting survives restart and marks uncertain charges unknown; alert routing tested against a local sink; rollback restores a healthy prior image; clean-machine rehearsal and recovery complete; resource/overhead results include methodology; limitations and failed experiments published honestly; learner can explain tradeoffs. No performance numbers in these plans are measurements.

## Repository status
Dedicated repository selected at G0: `https://github.com/pranjulya/traced-deployment-pipeline.git` (default branch `main`). This folder is its working tree and the planning package is committed as the initial baseline. The remote is currently PUBLIC: pushing it is publication and is not authorized until a G3-style review; nothing else may be pushed or published without explicit authorization. Open host items: the Docker Desktop daemon is not currently running, and its allocated CPU/RAM must be verified against the 4 vCPU / 8 GB envelope during phase 00/02. System Python is 3.9.6; the interpreter/runtime version is pinned in phase 00.

## Navigation
- [PRD](docs/product/PRD.md), [HLD](docs/architecture/HLD.md), [LLD](docs/architecture/LLD.md)
- [Phases](implementation/README.md), [evaluation](docs/evaluation/evaluation-strategy.md)
- [Operations](docs/operations/production-scenarios.md), [learning](Learning/README.md)
- [Sources](docs/architecture/sources.md), [review](docs/product/morning-review.md)
- [Accounting & API contract](docs/architecture/accounting-and-api-contract.md), [versions and pins](docs/architecture/versions-and-pins.md)
