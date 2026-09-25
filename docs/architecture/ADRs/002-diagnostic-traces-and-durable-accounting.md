# ADR 002: Diagnostic traces and durable accounting

Status: ACCEPTED (G0, 2026-09-25). Decision owner: project reviewer.

## Context
Project 09 must isolate operational learning while remaining independently repeatable.

## Recommended decision
Use OTel for diagnostics and SQLite WAL for unsampled attempt-level usage.

## Alternative
Trace-derived cost undercounts when sampling or export drops occur.

## Consequences
Must surface unknown charges and maintain reconciliation audit.

## Validation and revisit trigger
Crash between provider dispatch and completion must never fabricate zero cost. Revisit when measured scale or a changed product requirement invalidates this boundary. Acceptance is recorded only after G0 review; rejection updates master and affected phases.
