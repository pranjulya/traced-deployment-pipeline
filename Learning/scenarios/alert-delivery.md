# Alert fires but no one receives it

## Prediction
Write expected signals before the drill.

## Injection
Make local notification sink unavailable before firing a synthetic service alert.

## Diagnosis
Rule firing and delivery success are distinct; inspect Alertmanager routing, silence state and receiver errors.

## Recovery
Restore sink, prove received and resolved notifications, then inspect grouping for duplicates.

## Debrief
Can a dashboard screenshot prove end-to-end alert reliability? No; receiver evidence is required. Record detection and recovery times with sanitized evidence.
