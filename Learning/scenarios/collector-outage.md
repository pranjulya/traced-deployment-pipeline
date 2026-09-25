# Collector outage

## Prediction
Write expected signals before the drill.

## Injection
Stop Collector while deterministic requests continue.

## Diagnosis
Queue/drop metrics show loss; request success and ledger totals remain correct within workload budget. Missing traces are an acknowledged gap.

## Recovery
Restore Collector; confirm new traces arrive and memory remains bounded. Do not claim lost traces were recovered without evidence.

## Debrief
Why does fail-open telemetry differ from fail-closed accounting? Record detection and recovery times with sanitized evidence.
