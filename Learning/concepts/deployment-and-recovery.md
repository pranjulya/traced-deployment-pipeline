# A container is not a backup

Images define executable content; volumes hold state. Readiness controls whether work should be accepted; liveness reports whether the process exists. A single-host deployment is one failure domain. A compatible old image plus current ledger schema is needed for rollback.

## Exercise
Recreate a container and verify ledger persistence, then restore a consistent backup to a clean volume. Measure recovery rather than assuming it.

## Review question
Which assumption could invalidate this design at larger scale, and what measurement would justify a change?
