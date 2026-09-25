# Phase execution guide
Phases 00–01 COMPLETE (G1/G2 approved); Phase 02 IN_PROGRESS; phases 03–06 NOT_STARTED. Execute sequentially, opening each only after predecessor review. Phase 00 approves contracts and freezes tests; phases 01–05 build and verify one layer at a time; phase 06 produces release evidence. The authoritative scope, gates and Definition of Done are in ../Implementation.md.

| Phase | Depends on | Exit evidence |
|---|---|---|
| 00 Contract and fixture design | G0 owner review | approved scope, ADR log, expected fixtures |
| 01 Bounded agent and accounting | 00 | attempt/idempotency/crash checks |
| 02 Reproducible container deployment | 01 | clean start, persistence and rollback |
| 03 Correlated safe telemetry | 02 | parentage and canary checks |
| 04 Dashboards and alert delivery | 03 | totals reconciled and local sink receipt |
| 05 Failure drills and performance | 04 | incident and overhead report |
| 06 Release and learning evidence | 05 | clean-room rehearsal and reviewed bundle |

Every phase record must add implementation date, commit, actual commands, evidence paths, deviations, review decision and next-phase authorization. Leave planned checks distinct from executed checks. Reopen affected earlier phases when a changed contract invalidates evidence.

## Status transitions
NOT_STARTED → IN_PROGRESS → IMPLEMENTED → TESTED → REVIEWED → COMPLETE. COMPLETE requires recorded acceptance evidence and learner explanation. A missing check is not a pass; a review is not a test. Planning-only preparation changes none of these execution statuses.
