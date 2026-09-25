"""Deterministic ledger fixture for dashboard and alert checks.

Seeds known usage, unknown-charge attempts and two currencies so panel totals
can be compared against the ledger. Imported by tests; also usable as a script:

    python deploy/fixtures/load_ledger_fixture.py /tmp/p09-fixture.sqlite
"""

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.accounting import Ledger  # noqa: E402

PRICE_VERSION = "prices-2026-01-01"


def seed(ledger):
    """Populate deterministic runs/attempts; return a summary of expected totals."""
    # Run 1: two known USD attempts (observed + estimated).
    run_known = "fixture-run-known"
    _admit(ledger, run_known, "fixture-key-known")
    a1 = ledger.create_pending_attempt(run_known, 1, "fake", "fake-small")
    ledger.complete_attempt(
        a1, input_tokens=1000, output_tokens=500, usage_origin="provider",
        currency="USD", charge="0.000450000", charge_state="observed", price_version=PRICE_VERSION,
    )
    a2 = ledger.create_pending_attempt(run_known, 2, "fake", "fake-small")
    ledger.complete_attempt(
        a2, input_tokens=2000, output_tokens=1000, usage_origin="estimated",
        currency="USD", charge="0.000900000", charge_state="estimated", price_version=PRICE_VERSION,
    )

    # Run 2: one known EUR attempt (kept separate, never summed with USD).
    run_eur = "fixture-run-eur"
    _admit(ledger, run_eur, "fixture-key-eur")
    e1 = ledger.create_pending_attempt(run_eur, 1, "fake", "fake-eur")
    ledger.complete_attempt(
        e1, input_tokens=1000, output_tokens=500, usage_origin="provider",
        currency="EUR", charge="0.000600000", charge_state="observed", price_version=PRICE_VERSION,
    )

    # Run 3: one unknown-charge attempt (uncertainty must stay visible, not zero).
    run_unknown = "fixture-run-unknown"
    _admit(ledger, run_unknown, "fixture-key-unknown")
    u1 = ledger.create_pending_attempt(run_unknown, 1, "fake", "fake-small")
    ledger.unknown_attempt(u1)

    return {"run_ids": [run_known, run_eur, run_unknown]}


def _admit(ledger, run_id, key):
    # Deterministic admission with fixed timestamps is not required here, so a
    # plain insert keeps the fixture readable.
    with ledger._transaction() as conn:  # noqa: SLF001 - fixture only
        conn.execute(
            "INSERT INTO run_registry (run_id, principal_alias, key_digest, admitted_at, expires_at, state)"
            " VALUES (?,?,?,?,?,?)",
            (run_id, "demo-operator", f"digest-{key}", "2026-09-25T00:00:00+00:00",
             "2026-09-26T00:00:00+00:00", "completed"),
        )


def main(argv):
    db_path = argv[1] if len(argv) > 1 else "/tmp/p09-fixture.sqlite"
    ledger = Ledger(db_path)
    try:
        summary = seed(ledger)
        print("seeded", summary)
        print("aggregate", ledger.aggregate())
    finally:
        ledger.close()


if __name__ == "__main__":
    main(sys.argv)
