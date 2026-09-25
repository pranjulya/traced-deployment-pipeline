# Accounting and API contract

Status: FROZEN at Phase 00 (2026-09-25), subject to G1 review. This freezes decisions the fixtures encode. Changing any value here invalidates Phase 01 evidence and reopens Phase 00.

## Money representation
- Representation: exact decimal string, never float.
- Minor unit: nano (1 major unit = 1,000,000,000 nano-units).
- Storage scale: 9 decimal places.
- Rounding: `ROUND_HALF_EVEN`.
- Never-zero rule: an exact charge greater than zero is never stored as zero. If it would round to zero, store one nano-unit (`0.000000001`). An exact zero stores `0`.
- Rationale: the smallest fixture charge is `1.5E-7`, which a 6-decimal scale would silently zero, violating "never replace a known cost with zero". See `tests/fixtures/prices.json` -> `money`.

## Attempt state: two independent axes
`usage_origin` and `charge_state` are independent. Known usage does not imply a known charge.
- `usage_origin`: `provider` (tokens observed from provider), `estimated`, `unknown`.
- `charge_state`: `observed`, `estimated`, `unknown`, `reconciled`.
- A price-lookup miss keeps `usage_origin=provider` with `charge_state=unknown`. A post-dispatch crash keeps both `unknown`.
- Rule: if `charge_state=unknown`, the stored charge is null (absent), never a number. If `usage_origin=unknown`, then `charge_state` must be `unknown`.

## Attempt and run enums
- `status`: `pending`, `completed`, `failed`, `unknown`.
- `run_state`: `accepted`, `running`, `completed`, `failed`, `accounting_unknown`.
- Every actual provider attempt is accounted exactly once; attempt `ordinal` values are contiguous from 1.

## HTTP status and safe error codes
| Situation | Status | `safe_error_code` | Provider calls |
|---|---|---|---|
| Missing/invalid idempotency key | 400 | `MISSING_IDEMPOTENCY_KEY` | 0 |
| Body over 8 KiB | 400 | `PAYLOAD_TOO_LARGE` | 0 |
| Bad application credential | 401 | `UNAUTHENTICATED` | 0 |
| Duplicate principal + key | 409 | `DUPLICATE_REQUEST` | 0 (original only) |
| Provider auth/schema error | 502 | `PROVIDER_AUTH_ERROR` | 1 (never retried) |
| Tool failure | 502 | `TOOL_FAILURE` | per attempt |
| Transient errors exhausted | 502 | `PROVIDER_UNAVAILABLE` | ≤ 3 |
| Provider timeout after dispatch | 504 | `PROVIDER_TIMEOUT` | ≥ 1 |
| Pending commit failure (pre-dispatch) | 503 | `ACCOUNTING_UNAVAILABLE` | 0 |
| Completion commit failure (post-provider) | 503 | `ACCOUNTING_UNAVAILABLE` | 1 |
| Client cancel before dispatch | none | `CLIENT_CANCELLED` | 0 |

Only `429` and `500`-class errors are retryable, at most twice (three attempts total) within the 30 s deadline. Authentication and schema errors are terminal. A provider error that is known not to have processed the request is accounted as an observed zero, not as unknown.

## Restart classification (crash windows)
| Crash point | Durable state | Outcome |
|---|---|---|
| Before pending attempt commit | No attempt row | Durable state proves no dispatch: run `failed`, no charge invented |
| After pending commit, dispatch unproven | Pending attempt row | Run `accounting_unknown`; attempt becomes `unknown`; not auto-replayed |
| After dispatch | Pending attempt row | Run `accounting_unknown`; attempt becomes `unknown`; not auto-replayed |

A crash after admission never auto-replays. Uncertainty is surfaced, never silently zeroed.

## Source of truth
The machine-readable oracle is `tests/fixtures/cases.json`; self-consistency is enforced by `tests/test_fixture_oracle.py`.
