# Phase 02 — Container Deployment

Status: IMPLEMENTED — static checks pass; live rehearsal BLOCKED (Docker Desktop unavailable). Owner: learner + coding agent. Reviewer: main architect.

## Goal
Make a clean local deployment repeatable.
## Why
An unreproducible demo cannot support reliable operations.
## Prerequisites
01 reviewed; Docker Desktop running on the macOS reference host (arm64 Linux container runtime). All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Internal networks, persistent ledger, bounded resources and pinned images.
## Files
future deploy/; deployment runbook; tests/integration/. These are proposed future paths; create only those justified by the approved phase.
## Work sequence
1. Record runtime/image compatibility against Docker Desktop on arm64 and pin candidate digests; define separate private ingress and telemetry networks.
2. Package the API without embedded secrets; mount writable ledger and inject application/provider/HMAC credentials separately.
3. Define readiness around valid configuration and writable ledger; define resource/concurrency caps.
4. Write fresh-volume bootstrap, consistent backup, restart and prior-image rollback procedures.
5. Rehearse migration compatibility before any ledger schema change is accepted.

## Tests
Clean start, readiness, volume restart, non-root execution and prior-image rollback.
## Deterministic test oracle
| Case | Expected result |
|---|---|
| Clean host and fresh volume | Documented start reaches ready; one authenticated fixture completes |
| Container recreation | Ledger/run registry retained; duplicate key does not redispatch |
| Missing HMAC or application secret | Startup/readiness fails safely; no provider calls |
| Read-only ledger volume | Not ready; new execution rejected, existing evidence preserved |
| Collector unavailable | Verified in Phase 03 once the Collector exists; Phase 02 readiness depends only on a writable ledger and valid secrets |
| Prior image with compatible schema | Smoke execution works and totals remain consistent |
| Incompatible schema rollback | Procedure refuses unsafe downgrade; tested backup path required |
| Inspect host ports and image environment | No public admin services or baked-in secrets |

## Failure scenarios
Read-only volume; missing secret; incompatible schema; host memory pressure; Docker Desktop daemon stopped or VM under-allocated.
## Acceptance criteria
R02 passes; rollback and persistent accounting verified; no public admin ports. No result may be marked passing without recorded output.
## Learning objectives
Distinguish readiness from liveness and recoverability from HA.
## Interview questions
Why should Collector failure not fail application readiness? Answer using this phase's measured evidence and the relevant Learning page.
## Review gate and rollback
Check requirement mapping, privacy, bounded resource use and changed contracts. Revert this phase's app/config changes if its checks fail; preserve ledger data and avoid incompatible migrations. A rollback requiring data transformation needs a tested backup first.
## Completion record
Implementation commit: pending (recorded in the follow-up commit).
Created: deploy/Dockerfile (digest-pinned, non-root UID 10001), deploy/compose.yaml (loopback-only ingress, internal telemetry network, read-only root, cap_drop ALL, 1 CPU / 512 MB, named ledger volume, /health/ready healthcheck), deploy/.env.example, deploy/runbook.md, deploy/backup-ledger.sh, app/main.py (env wiring + restart classification), .dockerignore, tests/integration/test_deploy_config.py, tests/integration/live_deploy_check.sh.
Commands/results (2026-09-25):
- `.venv/bin/python -m pytest tests -q` → `67 passed` (57 Phase 01 + 10 deployment-config checks).
- `bash tests/integration/live_deploy_check.sh` → NOT RUN: Docker Desktop engine unavailable.
Environment blocker: `docker info` reports the daemon is down. `docker desktop start` returns "already running", but the backend socket (`~/Library/Containers/com.docker.docker/Data/backend.sock`) is absent and `open -a Docker` fails with `AppleEvent timed out (-1712)`. `kern.hv_support=1`, so this is a Docker Desktop session/launch issue, not missing virtualization support.
Requirement mapping: R02 (pinned single-host Compose deployment with health/readiness, persistent accounting and documented rollback) — configuration complete and statically verified; live clean-start/restart/rollback evidence pending.
Unverified oracle rows (need a running daemon): clean host and fresh volume; container recreation persistence; missing-secret readiness at runtime; read-only ledger volume; prior-image compatible-schema rollback; incompatible-schema refusal; host port and image-environment inspection.
Security/privacy: API published on loopback only; telemetry network internal; container non-root, read-only root filesystem, all capabilities dropped, no-new-privileges, bounded CPU/memory; secrets injected via env_file and never baked into the image (asserted statically).
Rollback impact: reverting this phase removes deploy/ and the integration checks; no ledger migration is introduced, so existing ledger data is unaffected.
Deviations: (1) live rehearsal blocked as above; (2) the Phase 02 oracle's "Collector unavailable" row is deferred to Phase 03 because no Collector exists yet.
Review decision: pending G2-style phase review, and pending the live rehearsal.
Next phase authorization: withheld — Phase 03 must not start until Phase 02 live checks pass and are reviewed.
