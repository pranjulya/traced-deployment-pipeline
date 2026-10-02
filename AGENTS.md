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

## Working habits
- Plan first: for a long task, state in 2-3 sentences what you think is wanted and start only after the owner says yes. Put steps and how each will be proven in the active phase file (no separate PLAN.md). After two failed tries on one step, stop, record what failed, and re-plan. When pausing, leave the phase file current so a new session can resume.
- Smallest change that works: no new dependencies, renames or refactors nobody asked for. Back up before deleting or overwriting. Weigh UX, DX (next developer) and AX (next agent) on tradeoffs.
- Subagents only when parallel reading pays off: explorer reads, worker edits, reviewer only reports. One job and a done condition each; never two agents on one file; verify a report's key claim before building on it.
- Own the bug: reproduce with the owner's steps first (can't? say what you need), fix the cause, rerun the same steps. Never silence an error to make it go away.
- Verify before saying done: run the tests and read the output yourself. For UI/dashboards, try to break them (empty input, double submit, refresh). An unrun check is not a pass; say so. Report in 2-3 lines: what you picked, what you gave up, why.
- Corrections: when the owner corrects you, add a "When X, do Y" line under Lessons. A repeated mistake means the lesson is unclear; rewrite it. Ask before changing anything above Lessons.

## Lessons
<!-- Newest on top. Delete what no longer applies. -->
- When claiming a repo fact (e.g. what is pushed), verify with a command first; don't assert from memory.
