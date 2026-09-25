# Evaluation strategy
Status: designed before implementation; no results exist.

## Test matrix and methodology
Use fixed fixtures for success, invalid input, provider 429/500/timeout, tool failure, cancellation, duplicate idempotency key, missing usage, price lookup miss, ledger write failure, exporter outage and process crash at accounting boundaries. Expected spans, attempts, outcomes and ledger totals are specified before code.

Correctness gate: 100% fixture assertions pass; each actual provider attempt accounted exactly once locally; duplicate completion events do not double count; unresolved external charge remains unknown. Privacy gate: zero synthetic sensitive canaries in all emitted/stored telemetry. Correlation gate: all spans in deterministic unsampled runs have expected parentage; sampled runs report expected gaps.

Performance experiment: record hardware, OS, container/image digests, model/provider, fixture version, concurrency, warmup and random seed. Compare identical 100-request workloads with instrumentation off/on in three alternating repetitions after 20 warmup requests. Report median, p95, counts, errors and raw sanitized results; do not compare live-provider noise with fake baseline. Proposed targets are in PRD; a miss triggers diagnosis and revised design or explicitly approved budget, not edited results.

Accounting reconciliation uses decimal arithmetic and a fixture price table with currency and effective date. Compare expected attempt totals with ledger and dashboard; tolerate scrape delay but no permanent double counting. Simulate retry charges, unknown usage, zero-fee local provider plus unknown compute cost, and schema migration/rollback.

Operations gate: local alert delivery meets stated window after firing; muted/no-traffic conditions do not spam; collector outage does not prevent successful fake requests; restore and prior-image rollback pass; measured RTO/RPO recorded. Diagnose three blinded injected incidents using only approved dashboards/traces/runbooks, target identification within 10 min each. If missed, document the blind spot.

Evidence bundle: environment manifest, fixture version, test output, sanitized traces/ledger aggregates, benchmark CSV, dashboard exports, failure timeline and limitation report. Phase 06 reruns release-critical checks; reports explicitly distinguish proposed targets from measured outcomes.

## Cross-project evidence contract
For P11 publication, each result record includes run_id, project_id=P09, source_commit, environment/hardware/software/model/dataset revisions, configuration digest, measurement protocol, sanitized raw artifacts with checksums, metrics with units and sample counts, and limitations. Unsupported or unmeasured fields are explicitly not measured, never invented. P12 consumes only approved summaries linked to this provenance, not mutable dashboard screenshots or unreviewed claims.

## Admission and accounting fault oracle
Verify atomic same-principal/key admission under simultaneous callers; required-key rejection; duplicate bodies ignored without execution; 409 metadata without stored answer; terminal expiry enabling a documented fresh execution; unresolved records retained beyond TTL; HMAC-key rotation preserving lookup; and database outage returning 503 with no redispatch. Inject post-provider completion-commit failure: no answer released, pending accounting remains recoverable and subsequent duplicate stays blocked.
