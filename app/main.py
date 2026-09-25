"""Container entrypoint wiring.

Builds settings, ledger, provider, tool and agent from the environment, runs
restart classification, and exposes the ASGI app for uvicorn.
"""

from .accounting import Ledger
from .agent import Agent
from .api import create_app
from .config import Settings
from .pricing import PriceTable
from .providers import FakeProvider
from .tools import LookupTool


def build_app():
    settings = Settings.from_env()
    ledger = Ledger(settings.db_path, settings.registry_ttl_seconds)
    ledger.recover_on_startup()
    agent = Agent(ledger, FakeProvider(), LookupTool(), PriceTable(), settings)
    return create_app(settings, ledger, agent)


app = build_app()
