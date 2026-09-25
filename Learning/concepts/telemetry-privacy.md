# Do not collect what you cannot safely retain

An allowlist is easier to audit than filtering arbitrary text. Exception messages, headers and dynamic metric labels are common leak paths. Generated correlation IDs are useful without recording user identity. Collector filtering cannot undo application logs already written.

## Exercise
Place synthetic secret markers in input, provider errors and tool errors; inspect every sink. Explain what debugging information was intentionally sacrificed.

## Review question
Which assumption could invalidate this design at larger scale, and what measurement would justify a change?
