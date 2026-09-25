# ADR 003: Content-free telemetry

Status: ACCEPTED (G0, 2026-09-25). Decision owner: project reviewer.

## Context
Project 09 must isolate operational learning while remaining independently repeatable.

## Recommended decision
Emit only explicitly allowlisted metadata; never capture payloads.

## Alternative
Redacting arbitrary raw payloads after export cannot reliably undo a leak.

## Consequences
Some debugging requires synthetic reproduction rather than viewing real text.

## Validation and revisit trigger
Canary inputs, exception strings and headers are absent in every backend. Revisit when measured scale or a changed product requirement invalidates this boundary. Acceptance is recorded only after G0 review; rejection updates master and affected phases.
