# ADR 004: Bounded agent fixture

Status: ACCEPTED (G0, 2026-09-25). Decision owner: project reviewer.

## Context
Project 09 must isolate operational learning while remaining independently repeatable.

## Recommended decision
Begin with a fake provider and one local read-only lookup tool.

## Alternative
Existing complex agent couples observability testing to unrelated behavior.

## Consequences
Proves operations independently; optional real integration follows.

## Validation and revisit trigger
All failures deterministic and no network provider needed for required checks. Revisit when measured scale or a changed product requirement invalidates this boundary. Acceptance is recorded only after G0 review; rejection updates master and affected phases.
