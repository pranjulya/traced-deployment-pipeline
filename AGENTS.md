# Coding-agent workflow
Single source of truth for every coding agent (CLAUDE.md only points here). Scope, phase status, gates and Definition of Done live in Implementation.md; read it first, then PRD → HLD → evaluation → LLD → ADRs → the active phase file. State assumptions; stop only for genuinely blocking ambiguity.

## Current state
Phases 00–01 COMPLETE; 02–04 IMPLEMENTED/TESTED with live checks BLOCKED (Docker Desktop unavailable); 05–06 NOT_STARTED. Code exists in `app/`, `deploy/`, `alerts/`, `dashboards/`, `tests/`. Implementation.md is authoritative; if this summary disagrees, fix it here.

## Rules
- One approved phase at a time, smallest change; do not alter other projects. Open a phase only after its predecessor's review.
- Before changes, inspect existing code and callers; use graph tools/coverage if available, otherwise say so and read source. Never claim graph coverage without evidence.
- Write meaningful fixture checks before nontrivial implementation. Run `pytest` before and after changes; record actual commands/results in the active phase file.
- Telemetry stays payload-free; accounting stays independent of traces. Never replace unknown cost with zero.
- Never invent benchmark results; never call the single-host reference high availability. Do not mark a phase COMPLETE without recorded live evidence.
- Contract changes update Implementation.md and affected docs/ADRs together.
- Review gate: requirement mapping, test evidence, failure handling, rollback impact, security/privacy check, learner explanation.
- No deployment, paid calls, external notification, or push/publication to the public remote without explicit authorization (G3). Pushing a working branch is not authorization to publish `main`.
- No `.claude` specialists/commands unless a repeated task justifies them.
