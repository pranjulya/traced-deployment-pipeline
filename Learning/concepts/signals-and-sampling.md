# Signals have different jobs

Metrics aggregate operational behavior; traces connect a request’s operations; a durable ledger preserves billable attempt state. A sampled trace is diagnostic evidence, not a complete event log. Histogram quantiles depend on count and bucket resolution. High-cardinality labels multiply storage cost.

## Exercise
Compare 100% versus 10% trace collection with the same ledger totals. Expect fewer traces, unchanged correct accounting, and possible missing failure traces under head sampling.

## Review question
Which assumption could invalidate this design at larger scale, and what measurement would justify a change?
