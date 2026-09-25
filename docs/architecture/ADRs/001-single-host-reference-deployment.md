# ADR 001: Single-host reference deployment

Status: ACCEPTED (G0, 2026-09-25). Decision owner: project reviewer.

## Context
Project 09 must isolate operational learning while remaining independently repeatable.

## Recommended decision
Use Docker Compose on one macOS reference host (Apple Silicon arm64, Docker Desktop Linux container runtime) with private service networking.

## Alternative
Kubernetes adds control-plane learning unrelated to this first deployment.

## Consequences
One host remains a failure domain; no HA claim.

## Validation and revisit trigger
Prove clean start, volume persistence and prior-image rollback on the macOS/Docker Desktop reference host; all pinned images must provide arm64 variants. Revisit when measured scale or a changed product requirement invalidates this boundary. Acceptance is recorded only after G0 review; rejection updates master and affected phases.
