import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.accounting import Ledger, LedgerUnavailable  # noqa: E402
from app.agent import Agent  # noqa: E402
from app.config import Settings  # noqa: E402
from app.pricing import PriceTable  # noqa: E402
from app.providers import FakeProvider  # noqa: E402
from app.tools import LookupTool  # noqa: E402
from app.api import key_digest  # noqa: E402

DEFAULT_KEY = "k" * 16


@pytest.fixture
def settings(tmp_path):
    return Settings(
        app_secret="app-secret",
        hmac_secret="hmac-secret",
        db_path=str(tmp_path / "ledger.sqlite"),
    )


@pytest.fixture
def ledger(settings):
    led = Ledger(settings.db_path, settings.registry_ttl_seconds)
    yield led
    led.close()


def admit_run(ledger, settings, key=DEFAULT_KEY):
    digest = key_digest(settings.hmac_secret, settings.principal_alias, key)
    run_id, existing = ledger.admit(settings.principal_alias, digest)
    assert existing is None
    return run_id


def build_agent(ledger, settings, behaviors=None, fail_tool_next=0, price_table=None):
    provider = FakeProvider(behaviors)
    tool = LookupTool(fail_next=fail_tool_next)
    agent = Agent(ledger, provider, tool, price_table or PriceTable(), settings)
    return agent, provider, tool


@pytest.fixture
def agent_factory(settings, ledger):
    def factory(behaviors=None, fail_tool_next=0):
        return build_agent(ledger, settings, behaviors, fail_tool_next)

    return factory


class FailingLedger(Ledger):
    """Wraps a real ledger but fails a chosen commit path."""

    def __init__(self, *args, fail_on, **kwargs):
        super().__init__(*args, **kwargs)
        self.fail_on = fail_on

    def create_pending_attempt(self, *args, **kwargs):
        if self.fail_on == "create_pending":
            raise LedgerUnavailable("injected create_pending failure")
        return super().create_pending_attempt(*args, **kwargs)

    def complete_attempt(self, *args, **kwargs):
        if self.fail_on == "complete":
            raise LedgerUnavailable("injected complete_attempt failure")
        return super().complete_attempt(*args, **kwargs)
