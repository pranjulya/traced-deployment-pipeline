"""Phase 01 oracle checks at the agent boundary.

Case ids mirror tests/fixtures/cases.json so the frozen oracle and the
implementation stay in step.
"""

from datetime import date

import pytest

from app.agent import Agent, AgentError
from app.pricing import PriceTable
from app.providers import FakeProvider
from app.tools import LookupTool
from tests.conftest import FailingLedger, admit_run


def _single(ledger, run_id):
    attempts = ledger.attempts_for(run_id)
    assert len(attempts) == 1
    return attempts[0]


def test_success_single_attempt(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, provider, tool = agent_factory()

    result = agent.execute(run_id)

    attempt = _single(ledger, run_id)
    assert attempt["status"] == "completed"
    assert attempt["charge_state"] == "observed"
    assert attempt["charge"] == "0.000450000"
    assert ledger.run_totals(run_id) == {"USD": "0.000450000"}
    assert provider.calls == 1 and tool.calls == 1
    assert result.answer == "synthetic answer"


def test_provider_retry_success(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, provider, _ = agent_factory(["server_error", "success"])

    agent.execute(run_id)

    attempts = ledger.attempts_for(run_id)
    assert [a["status"] for a in attempts] == ["failed", "completed"]
    assert attempts[0]["charge"] == "0.000000000"
    assert attempts[1]["charge"] == "0.000450000"
    assert provider.calls == 2
    assert ledger.run_totals(run_id) == {"USD": "0.000450000"}


def test_provider_429_then_success(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, provider, _ = agent_factory(["rate_limited", "success"])

    agent.execute(run_id)

    assert provider.calls == 2
    assert ledger.run_totals(run_id) == {"USD": "0.000450000"}


def test_provider_retry_exhausted(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, provider, _ = agent_factory(["server_error", "server_error", "server_error"])

    with pytest.raises(AgentError) as excinfo:
        agent.execute(run_id)

    assert excinfo.value.safe_error_code == "PROVIDER_UNAVAILABLE"
    assert len(ledger.attempts_for(run_id)) == 3
    assert provider.calls == 3


def test_provider_auth_error_not_retried(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, provider, _ = agent_factory(["auth_error"])

    with pytest.raises(AgentError) as excinfo:
        agent.execute(run_id)

    assert excinfo.value.safe_error_code == "PROVIDER_AUTH_ERROR"
    assert provider.calls == 1
    assert len(ledger.attempts_for(run_id)) == 1


def test_provider_timeout_unknown(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, _, _ = agent_factory(["timeout"])

    with pytest.raises(AgentError) as excinfo:
        agent.execute(run_id)

    assert excinfo.value.safe_error_code == "PROVIDER_TIMEOUT"
    assert excinfo.value.http_status == 504
    attempt = _single(ledger, run_id)
    assert attempt["status"] == "unknown"
    assert attempt["charge"] is None
    assert attempt["charge_state"] == "unknown"
    assert ledger.run_totals(run_id) == {}
    assert ledger.get_run(run_id)["state"] == "failed"


def test_missing_usage_keeps_charge_unknown(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, _, _ = agent_factory(["no_usage"])

    agent.execute(run_id)

    attempt = _single(ledger, run_id)
    assert attempt["status"] == "completed"
    assert attempt["usage_origin"] == "unknown"
    assert attempt["charge"] is None
    assert ledger.run_totals(run_id) == {}


def test_price_lookup_miss_keeps_charge_unknown(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, _, _ = agent_factory()

    agent.execute(run_id, price_date=date(2025, 1, 1))

    attempt = _single(ledger, run_id)
    assert attempt["usage_origin"] == "provider"
    assert attempt["charge_state"] == "unknown"
    assert attempt["charge"] is None
    assert ledger.run_totals(run_id) == {}


def test_tiny_charge_not_zeroed(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, _, _ = agent_factory(["tiny"])

    agent.execute(run_id)

    assert _single(ledger, run_id)["charge"] == "0.000000750"
    assert ledger.run_totals(run_id) == {"USD": "0.000000750"}


def test_tool_failure_keeps_provider_charge(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, _, tool = agent_factory(fail_tool_next=1)

    with pytest.raises(AgentError) as excinfo:
        agent.execute(run_id)

    assert excinfo.value.safe_error_code == "TOOL_FAILURE"
    assert tool.calls == 1
    assert _single(ledger, run_id)["charge"] == "0.000450000"
    assert ledger.run_totals(run_id) == {"USD": "0.000450000"}
    assert ledger.get_run(run_id)["state"] == "failed"


def test_currency_eur_separate(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, _, _ = agent_factory()

    agent.execute(run_id, model="fake-eur")

    assert ledger.run_totals(run_id) == {"EUR": "0.000600000"}


def test_zero_fee_local_provider(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, _, _ = agent_factory()

    agent.execute(run_id, model="local-fake")

    assert _single(ledger, run_id)["charge"] == "0.000000000"
    assert ledger.run_totals(run_id) == {"USD": "0.000000000"}


def test_client_cancelled_before_dispatch(settings, ledger, agent_factory):
    run_id = admit_run(ledger, settings)
    agent, provider, _ = agent_factory()

    with pytest.raises(AgentError) as excinfo:
        agent.execute(run_id, cancel_check=lambda: True)

    assert excinfo.value.safe_error_code == "CLIENT_CANCELLED"
    assert provider.calls == 0
    assert ledger.attempts_for(run_id) == []
    assert ledger.get_run(run_id)["state"] == "failed"


def test_ledger_fail_before_dispatch_makes_no_call(settings):
    failing = FailingLedger(settings.db_path + "-pre", fail_on="create_pending")
    try:
        run_id = admit_run(failing, settings)
        provider = FakeProvider()
        agent = Agent(failing, provider, LookupTool(), PriceTable(), settings)

        with pytest.raises(AgentError) as excinfo:
            agent.execute(run_id)

        assert excinfo.value.safe_error_code == "ACCOUNTING_UNAVAILABLE"
        assert excinfo.value.http_status == 503
        assert provider.calls == 0
        assert failing.attempts_for(run_id) == []
    finally:
        failing.close()


def test_ledger_fail_after_provider_withholds_answer(settings):
    failing = FailingLedger(settings.db_path + "-post", fail_on="complete")
    try:
        run_id = admit_run(failing, settings)
        provider = FakeProvider()
        agent = Agent(failing, provider, LookupTool(), PriceTable(), settings)

        with pytest.raises(AgentError) as excinfo:
            agent.execute(run_id)

        assert excinfo.value.safe_error_code == "ACCOUNTING_UNAVAILABLE"
        assert provider.calls == 1
        assert _single(failing, run_id)["status"] == "unknown"
        assert failing.get_run(run_id)["state"] == "accounting_unknown"
        assert failing.run_totals(run_id) == {}
    finally:
        failing.close()
