"""Checks the deterministic ledger fixture reconciles (Phase 04, R05)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fixture_module():
    spec = importlib.util.spec_from_file_location(
        "load_ledger_fixture", ROOT / "deploy" / "fixtures" / "load_ledger_fixture.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixture_aggregates_match_expected_totals(settings, ledger):
    fixture_module().seed(ledger)

    agg = ledger.aggregate()

    assert agg["known_charge"] == {"USD": "0.001350000", "EUR": "0.000600000"}
    assert agg["unknown_attempts"] == 1
    assert agg["total_attempts"] == 4
    assert abs(agg["coverage_ratio"] - 0.75) < 1e-9


def test_metrics_expose_currencies_separately(settings, ledger):
    from app.telemetry import Telemetry

    fixture_module().seed(ledger)
    telemetry = Telemetry()
    telemetry.metrics.set_ledger_aggregates(ledger.aggregate())
    text = telemetry.metrics.render()

    assert 'p09_known_charge_nano_total{currency="USD"}' in text
    assert 'p09_known_charge_nano_total{currency="EUR"}' in text
    assert "p09_unknown_attempts" in text
    assert "p09_usage_coverage_ratio" in text
