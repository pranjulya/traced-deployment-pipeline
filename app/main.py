"""Container entrypoint wiring.

Builds settings, ledger, provider, tool, telemetry and agent from the
environment, runs restart classification, and exposes the ASGI app for uvicorn.
"""

import os

from .accounting import Ledger
from .agent import Agent
from .api import create_app
from .config import Settings
from .pricing import PriceTable
from .providers import FakeProvider
from .telemetry import NoopSpanExporter, Telemetry
from .tools import LookupTool


def build_telemetry():
    endpoint = os.environ.get("P09_OTLP_ENDPOINT")
    exporter = NoopSpanExporter()
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=endpoint)
    return Telemetry(
        exporter=exporter,
        head_sample_rate=float(os.environ.get("P09_TRACE_HEAD_RATE", "1.0")),
        deployment_revision=os.environ.get("P09_REVISION", "dev"),
    )


def build_app():
    settings = Settings.from_env()
    ledger = Ledger(settings.db_path, settings.registry_ttl_seconds)
    ledger.recover_on_startup()
    telemetry = build_telemetry()
    agent = Agent(ledger, FakeProvider(), LookupTool(), PriceTable(), settings, telemetry=telemetry)
    return create_app(settings, ledger, agent, telemetry=telemetry)


app = build_app()
