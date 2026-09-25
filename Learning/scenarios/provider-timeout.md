# Provider timeout after dispatch

## Prediction
Write expected signals before the drill.

## Injection
Inject delayed completion beyond request deadline.

## Diagnosis
Expect bounded retries, timeout spans and unknown charge when no usage evidence returns. Check attempt/request ratio before blaming tool latency.

## Recovery
Disable injection; reconcile known provider records; verify no unbounded retry loop.

## Debrief
Would a client retry with the same idempotency key create new work? It must not. Record detection and recovery times with sanitized evidence.
