"""Static validation of the Grafana dashboard (Phase 04, R05)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = json.loads((ROOT / "dashboards" / "p09-overview.json").read_text(encoding="utf-8"))


def panel_by_title(fragment):
    return [panel for panel in DASH["panels"] if fragment in panel["title"]]


def test_required_panels_present():
    titles = " | ".join(panel["title"] for panel in DASH["panels"])
    for needed in (
        "Service health",
        "Requests in 5m",
        "Error ratio",
        "Latency",
        "Retry amplification",
        "Provider attempts",
        "Telemetry drops",
        "Known charge by currency",
        "Unknown-charge attempts",
        "Usage coverage",
        "Host resources",
    ):
        assert needed in titles, needed


def test_currency_variable_is_declared():
    names = [var["name"] for var in DASH["templating"]["list"]]
    assert "currency" in names


def test_cost_panel_selects_currency_never_mixes():
    panel = panel_by_title("Known charge by currency")[0]
    assert all("currency" in target["expr"] for target in panel["targets"])


def test_latency_panel_shows_percentiles_and_description():
    panel = panel_by_title("Latency")[0]
    exprs = " ".join(target["expr"] for target in panel["targets"])
    for quantile in ("0.50", "0.95", "0.99"):
        assert quantile in exprs
    assert panel.get("description")


def test_unknown_shown_separately():
    assert panel_by_title("Unknown-charge attempts")


def test_no_identifier_or_payload_labels_in_queries():
    text = json.dumps(DASH)
    for forbidden in ("run_id", "trace_id", "principal", "idempotency_key", "prompt", "tool_arguments"):
        assert forbidden not in text, forbidden
