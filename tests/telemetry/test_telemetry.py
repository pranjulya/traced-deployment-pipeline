"""Phase 03 telemetry checks: parentage, privacy, sampling and export loss."""

import json
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from app.agent import Agent
from app.api import create_app
from app.pricing import PriceTable
from app.providers import FakeProvider
from app.telemetry import FailingSpanExporter, InMemorySpanExporter, Telemetry
from app.tools import LookupTool
from tests.conftest import admit_run

ROOT = Path(__file__).resolve().parents[2]
CANARIES = json.loads((ROOT / "tests" / "fixtures" / "canaries.json").read_text(encoding="utf-8"))["canaries"]
CANARY_VALUES = [c["value"] for c in CANARIES]


def telemetry_with(exporter=None, rate=1.0):
    return Telemetry(exporter=exporter or InMemorySpanExporter(), head_sample_rate=rate)


def agent_with(ledger, settings, telemetry, behaviors=None, tool=None):
    provider = FakeProvider(behaviors)
    agent = Agent(ledger, provider, tool or LookupTool(), PriceTable(), settings, telemetry=telemetry)
    return agent, provider


def spans_of(telemetry):
    return telemetry.exporter.sink.spans


def dump_spans(telemetry):
    parts = []
    for span in spans_of(telemetry):
        parts.append(span.name)
        parts.append(json.dumps({k: str(v) for k, v in (span.attributes or {}).items()}, default=str))
        for event in span.events:
            parts.append(event.name)
            parts.append(json.dumps({k: str(v) for k, v in (event.attributes or {}).items()}, default=str))
    return " ".join(parts)


def test_success_parentage(settings, ledger):
    telemetry = telemetry_with()
    agent, _ = agent_with(ledger, settings, telemetry)
    run_id = admit_run(ledger, settings)

    agent.execute(run_id)

    spans = spans_of(telemetry)
    assert sorted(span.name for span in spans) == ["agent.run", "provider.attempt", "tool.lookup"]
    root = next(s for s in spans if s.name == "agent.run")
    assert root.parent is None
    for child in (s for s in spans if s.name != "agent.run"):
        assert child.parent is not None
        assert child.parent.span_id == root.context.span_id


def test_allowlist_matches_frozen_fixture():
    runtime = json.loads((ROOT / "app" / "telemetry-allowlist.json").read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "tests" / "fixtures" / "telemetry-allowlist.json").read_text(encoding="utf-8"))
    assert runtime == fixture


def test_canaries_absent_from_all_sinks(settings, ledger, caplog):
    telemetry = telemetry_with()
    agent, _ = agent_with(ledger, settings, telemetry)
    run_id = admit_run(ledger, settings)
    prompt = " ".join(CANARY_VALUES)

    with caplog.at_level(logging.DEBUG):
        agent.execute(run_id, messages=[{"role": "user", "content": prompt}])

    dump = dump_spans(telemetry) + telemetry.metrics.render() + caplog.text
    for canary in CANARY_VALUES:
        assert canary not in dump, canary
    assert "tool_arguments" not in dump


def test_exception_text_is_not_captured(settings, ledger):
    class ExplodingProvider(FakeProvider):
        def call(self, messages, model, deadline):
            raise RuntimeError("EXC_CANARY internal failure at 10.0.0.1")

    telemetry = telemetry_with()
    agent = Agent(ledger, ExplodingProvider(), LookupTool(), PriceTable(), settings, telemetry=telemetry)
    run_id = admit_run(ledger, settings)

    try:
        agent.execute(run_id)
    except RuntimeError:
        pass

    dump = dump_spans(telemetry)
    assert "EXC_CANARY" not in dump
    assert "RuntimeError" not in dump


def test_user_supplied_labels_are_dropped(settings, ledger):
    telemetry = telemetry_with()
    with telemetry.span("agent.run", {"operation": "run", "user_supplied_label": "CANARY_LABEL"}):
        pass

    span = spans_of(telemetry)[0]
    assert "user_supplied_label" not in span.attributes
    assert telemetry.dropped_attributes >= 1


def test_metrics_contain_no_ids_or_payloads(settings, ledger):
    telemetry = telemetry_with()
    agent, _ = agent_with(ledger, settings, telemetry)
    run_id = admit_run(ledger, settings)
    agent.execute(run_id, messages=[{"role": "user", "content": CANARY_VALUES[0]}])

    text = telemetry.metrics.render()
    for forbidden in ("run_id", "trace_id", "principal", "idempotency", "prompt", "output"):
        assert forbidden not in text, forbidden
    for canary in CANARY_VALUES:
        assert canary not in text, canary


def test_head_sampling_reduces_traces_but_not_accounting(settings, ledger):
    telemetry = telemetry_with(rate=0.1)
    agent, _ = agent_with(ledger, settings, telemetry)

    run_ids = []
    for index in range(60):
        run_id = admit_run(ledger, settings, key=f"sample{index:010d}")
        run_ids.append(run_id)
        agent.execute(run_id)

    assert 0 < telemetry.spans_exported < 60
    # Accounting is unsampled: every run's charge is still recorded.
    for run_id in run_ids:
        assert ledger.run_totals(run_id) == {"USD": "0.000450000"}


def test_exporter_outage_is_nonblocking_and_counted(settings, ledger):
    telemetry = Telemetry(exporter=FailingSpanExporter(), head_sample_rate=1.0)
    agent, _ = agent_with(ledger, settings, telemetry)
    run_id = admit_run(ledger, settings)

    result = agent.execute(run_id)

    assert result.answer == "synthetic answer"
    assert telemetry.spans_dropped > 0
    assert ledger.run_totals(run_id) == {"USD": "0.000450000"}


def test_http_headers_and_route_metrics_are_content_free(settings, ledger):
    telemetry = telemetry_with()
    agent, _ = agent_with(ledger, settings, telemetry)
    client = TestClient(create_app(settings, ledger, agent, telemetry=telemetry))

    response = client.post(
        "/v1/runs",
        headers={
            "Authorization": "Bearer app-secret",
            "Idempotency-Key": "k" * 16,
            "X-Canary": CANARY_VALUES[0],
        },
        json={"input": CANARY_VALUES[2]},
    )
    assert response.status_code == 200

    dump = dump_spans(telemetry) + telemetry.metrics.render()
    for canary in CANARY_VALUES:
        assert canary not in dump, canary
    assert "X-Canary" not in dump
