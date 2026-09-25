import threading

from app.api import key_digest
from tests.conftest import DEFAULT_KEY, admit_run


def test_admit_then_duplicate_returns_same_run(settings, ledger):
    run_id = admit_run(ledger, settings)
    digest = key_digest(settings.hmac_secret, settings.principal_alias, DEFAULT_KEY)
    again, existing = ledger.admit(settings.principal_alias, digest)
    assert again is None
    assert existing["run_id"] == run_id


def test_concurrent_admission_has_single_winner(settings, ledger):
    digest = key_digest(settings.hmac_secret, settings.principal_alias, DEFAULT_KEY)
    barrier = threading.Barrier(8)
    outcomes = []

    def worker():
        barrier.wait()
        run_id, existing = ledger.admit(settings.principal_alias, digest)
        outcomes.append(run_id if run_id else "duplicate")

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    winners = [o for o in outcomes if o != "duplicate"]
    assert len(winners) == 1
    assert outcomes.count("duplicate") == 7


def test_totals_never_mix_currencies_and_exclude_unknown(settings, ledger):
    run_id = admit_run(ledger, settings)
    usd = ledger.create_pending_attempt(run_id, 1, "fake", "fake-small")
    ledger.complete_attempt(usd, input_tokens=1000, output_tokens=500, usage_origin="provider",
                            currency="USD", charge="0.000450000", charge_state="observed",
                            price_version="prices-2026-01-01")
    eur = ledger.create_pending_attempt(run_id, 2, "fake", "fake-eur")
    ledger.complete_attempt(eur, input_tokens=1000, output_tokens=500, usage_origin="provider",
                            currency="EUR", charge="0.000600000", charge_state="observed",
                            price_version="prices-2026-01-01")
    unknown = ledger.create_pending_attempt(run_id, 3, "fake", "fake-small")
    ledger.unknown_attempt(unknown)

    assert ledger.run_totals(run_id) == {"USD": "0.000450000", "EUR": "0.000600000"}


def test_stored_rows_exclude_raw_key_prompt_and_answer(settings, ledger, agent_factory):
    raw_key = "SECRETKEY_rawvalue_1234"
    assert len(raw_key) >= 16
    run_id = admit_run(ledger, settings, key=raw_key)
    agent, _, _ = agent_factory()
    agent.execute(run_id)

    registry = ledger._conn.execute("SELECT * FROM run_registry").fetchall()
    attempts = ledger._conn.execute("SELECT * FROM usage_attempt").fetchall()
    dump = " ".join(str(tuple(row)) for row in list(registry) + list(attempts))

    assert raw_key not in dump
    assert "synthetic answer" not in dump
    assert "CANARY_PROMPT" not in dump
    assert ledger.get_run(run_id)["key_digest"] != raw_key


def test_recover_pending_attempt_becomes_unknown(settings, ledger):
    run_id = admit_run(ledger, settings)
    ledger.create_pending_attempt(run_id, 1, "fake", "fake-small")

    actions = ledger.recover_on_startup()

    assert actions == [(run_id, "accounting_unknown")]
    assert ledger.attempts_for(run_id)[0]["status"] == "unknown"
    assert ledger.get_run(run_id)["state"] == "accounting_unknown"


def test_recover_without_pending_proves_no_dispatch(settings, ledger):
    run_id = admit_run(ledger, settings)

    actions = ledger.recover_on_startup()

    assert actions == [(run_id, "failed")]
    assert ledger.get_run(run_id)["state"] == "failed"
    assert ledger.run_totals(run_id) == {}
