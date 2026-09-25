"""Static validation of Prometheus alert rules (Phase 04, R06)."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RULES = yaml.safe_load((ROOT / "alerts" / "prometheus-rules.yaml").read_text(encoding="utf-8"))
RUNBOOKS = (ROOT / "docs" / "operations" / "runbooks.md").read_text(encoding="utf-8")


def all_rules():
    return [rule for group in RULES["groups"] for rule in group["rules"]]


def by_name():
    return {rule["alert"]: rule for rule in all_rules()}


def test_every_alert_links_to_a_runbook_section():
    for rule in all_rules():
        runbook = rule["annotations"]["runbook"]
        assert runbook.startswith("docs/operations/runbooks.md#")
        anchor = runbook.split("#", 1)[1]
        assert f"## {anchor}" in RUNBOOKS, anchor


def test_every_alert_has_actionable_labels():
    for rule in all_rules():
        labels = rule["labels"]
        assert labels["severity"] in ("critical", "warning")
        assert labels["owner"]
        assert labels["service"]
        assert rule["annotations"]["summary"]


def test_labels_carry_no_identifiers():
    text = json.dumps(RULES)
    for forbidden in ("run_id", "trace_id", "instance", "idempotency_key", "prompt"):
        assert forbidden not in text, forbidden


def test_error_and_timeout_rules_require_minimum_traffic_and_window():
    rules = by_name()
    for name in ("P09ServiceErrorRateHigh", "P09ProviderTimeoutRateHigh"):
        rule = rules[name]
        assert ">= 20" in rule["expr"]
        assert rule["for"] == "2m"


def test_ledger_failure_is_immediate():
    assert "for" not in by_name()["P09LedgerWriteFailure"]


def test_rules_reference_only_metrics_the_app_emits():
    emitted = {
        "p09_requests_total",
        "p09_provider_attempts_total",
        "p09_provider_timeouts_total",
        "p09_ledger_write_failures_total",
        "p09_telemetry_drops_total",
    }
    for rule in all_rules():
        for name in re.findall(r"p09_[a-z0-9_]+", rule["expr"]):
            assert name in emitted, name
