# Phase 00 — Contract And Fixtures

Status: NOT_STARTED. Owner: learner + coding agent. Reviewer: main architect. No implementation performed.

## Goal
Freeze the operational contract before code.
## Why
Avoid confusing dashboard appearance with system correctness.
## Prerequisites
G0 scope review; local host inventory. All previous phases must be reviewed COMPLETE before starting.
## Architecture impact
Select bounded interfaces, ADRs, price fixture and privacy schema.
## Files
docs/product/PRD.md; docs/architecture/*; future tests/fixtures/. These are proposed future paths; create only those justified by the approved phase.
## Work sequence
1. Read master, applicable ADRs and predecessor evidence; restate the contract.
2. Define the smallest deterministic check for this phase's success and failure cases.
3. Implement only the phase boundary; preserve earlier acceptance checks.
4. Run checks, record actual evidence and explain one representative failure to the reviewer.
## Tests
Review deterministic expected runs, cost examples and threat cases.
## Failure scenarios
Missing GPU/provider; insufficient RAM; unsupported histogram integration.
## Acceptance criteria
ADR choices recorded; fixture oracle reviewed; versions and resource budget selected. No result may be marked passing without recorded output.
## Learning objectives
Explain metrics versus traces versus ledger truth.
## Interview questions
Why must accounting survive trace loss? Answer using this phase's measured evidence and the relevant Learning page.
## Review gate and rollback
Check requirement mapping, privacy, bounded resource use and changed contracts. Revert this phase's app/config changes if its checks fail; preserve ledger data and avoid incompatible migrations. A rollback requiring data transformation needs a tested backup first.
## Completion record
Implementation commit: pending. Commands/results: pending. Evidence paths: pending. Deviations: pending. Review decision: pending. Next phase authorization: pending.
